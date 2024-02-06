from web3 import Web3
from web3.middleware import geth_poa_middleware
import os
from dotenv import load_dotenv
from subgraph_api import SubgraphQuery
import json
from collections import defaultdict
import datetime
import time
import pickledb

db = pickledb.load("_txfee_cache.db", False)

EVM_DECIMALS = 1e18  # standard EVM currency has 18 decimals

load_dotenv()  # take environment variables from .env
w3 = dict()
HTTP_PROVIDER_ETH: str = os.environ.get("HTTP_PROVIDER_ETH")
w3["ETH"] = Web3(Web3.HTTPProvider(HTTP_PROVIDER_ETH))
print(f"Current ETH block number: {w3['ETH'].eth.block_number}")
HTTP_PROVIDER_BSC: str = os.environ.get("HTTP_PROVIDER_BSC")
w3["BSC"] = Web3(Web3.HTTPProvider(HTTP_PROVIDER_BSC))
# remove POA 32-byte extraData field since BSC is POA w/97 bytes
w3["BSC"].middleware_onion.inject(geth_poa_middleware, layer=0)
print(f"Current BSC block number: {w3['BSC'].eth.block_number}")


def get_abi(filepath):
    with open(filepath) as f:
        abi_json = json.load(f)
    return abi_json


ERC20_ABI = get_abi(os.path.join("web3_api", "ref", "token_abi.json"))


class TokenAmount:
    def __init__(self, symbol: str, addr: str, amount: float, spot_price=None, total_usd=None):
        self.symbol = symbol
        self.addr = addr
        self.amount = amount
        if spot_price is None and total_usd is None:
            self.spot_price = ""
            self.total_usd = "equal"
            return
        self.spot_price = "" if spot_price is None else spot_price
        self.total_usd = "" if total_usd is None else total_usd


class SwapSummary:
    def __init__(self, sent: TokenAmount, received: TokenAmount, book_fee_with: str, fee_chain: str,
                 tx_hash: str, date_time: str):
        self.sent = sent
        self.received = received
        self.book_fee_with = book_fee_with
        self.fee_chain = fee_chain
        self.tx_hash = tx_hash
        self.date_time = date_time

    @staticmethod
    def col_headers():
        return [
            'DateTime',
            'SellAsset',
            'SellQty',
            'SellSpotPriceUSD',
            'SellTotalUSD',
            'BuyAsset',
            'BuyQty',
            'BuySpotPriceUSD',
            'BuyTotalUSD',
            'BookFeeWith',
            'FeeChain1',
            'FeeTx1'
        ]

    def export_row(self):
        return [
            self.date_time,
            self.sent.symbol,
            self.sent.amount,
            self.sent.spot_price,
            self.sent.total_usd,
            self.received.symbol,
            self.received.amount,
            self.received.spot_price,
            self.received.total_usd,
            self.book_fee_with,
            self.fee_chain,
            self.tx_hash
        ]


class Exchange:
    def __init__(self, name: str, chain: str, method: str):
        """
        :param name: str e.g. "sushiswap"
        :param chain: str e.g. "ETH"
        :param method: str e.g. "Swap Eth for Exact Tokens
        """
        self.name = name
        self.chain = chain
        self.method = method


class PunkSummary:
    def __init__(self, tx_hash: str, punk_id: int, val_eth: float, to_address: str):
        self.tx_hash = tx_hash
        self.punk_id = punk_id
        self.val_eth = val_eth
        self.to_address = to_address

    @staticmethod
    def col_headers():
        return [
            'tx_hash',
            'punk_id',
            'val_eth',
            'to_address'
        ]

    def export_row(self):
        return [
            self.tx_hash,
            self.punk_id,
            self.val_eth,
            self.to_address
        ]


class Web3Query:

    supportedChains = w3.keys()
    supportedExchanges = [{"dex": "sushiswap", "chain": "ETH"}]
    _chainAddrToSymbolDecimalsCache = defaultdict(dict)
    _chainAddrToSymbolDecimalsCache["ETH"]["0x0000000000000000000000000000000000000000"] = ("ETH", 18)

    def __init__(self):
        # initialize etherscan web3_api
        self.test = "test"

    @staticmethod
    def get_tx_fee(tx_hash: str, chain: str, convert_to_usd: bool = True, overwrite_cache: bool = False):
        """
        This function returns tx fee in USD given a tx_hash
        :param tx_hash: str hash of tx to retrieve
        :param chain: str indicating which chain to query.
                      supported chains defined in Web3Query.supportedChains
        :param return_in_usd: bool=True will translate from chain currency to USD if True, otherwise returns
                      fee in chain fee currency
        :return: transaction fee in usd
        """
        cache_key = chain + tx_hash + "usd_" + str(convert_to_usd)
        if (not overwrite_cache):
            # check if cached value
            # print("getting key: " + cache_key)
            _cached_val = db.get(cache_key)
            if (not _cached_val == False):
                return _cached_val


        if chain not in Web3Query.supportedChains:
            raise KeyError(f"RPC for chain {chain} not supported!")
        # get gas used
        _tx_receipt = w3[chain].eth.get_transaction_receipt(tx_hash)
        gas_used = _tx_receipt.gasUsed
        gas_price = w3[chain].eth.get_transaction(tx_hash).gasPrice
        # base currency fee
        base_currency_fee = gas_used * gas_price / EVM_DECIMALS
        if not convert_to_usd:
            print("caching key: " + cache_key + " to " + str(base_currency_fee))
            db.set(cache_key, base_currency_fee)
            db.dump()
            return base_currency_fee
        # convert to usd via gql dex price at this block
        gas_asset_price_usd = None
        try:
            if chain == "ETH":
                gas_asset_price_usd = float(SubgraphQuery.get_eth_price_at_block(
                    _tx_receipt.blockNumber)
                )
            elif chain == "BSC":
                gas_asset_price_usd = float(SubgraphQuery.get_bnb_price_at_bsc_block(
                    _tx_receipt.blockNumber)
                )
        except ValueError as e:
            print(f"Error while getting gas asset price for tx: {tx_hash}. \n" +
                  "May be a gap in BSC pancakeswap v1 vs. v2 subgraphs. \n" +
                  "If a subgraph issue, please manually fill in gas asset override price in input table.")
            raise e
        base_currency_fee_usd = base_currency_fee * gas_asset_price_usd
        print("caching key: " + cache_key + " to " + str(base_currency_fee_usd))
        db.set(cache_key, base_currency_fee_usd)
        db.dump()
        return base_currency_fee_usd

    @staticmethod
    def get_token_symbol_and_decimals(addr: str, chain: str):
        """
        Returns token symbol for a given address (caches)
        :param addr: str Address of token to get symbol for (e.g. 0x1234...fff)
        :param chain: chain on which token resides (e.g. ETH, BSC, etc.)
        :return: tuple of:
                    symbol: string symbol of token (e.g. UNI, ETH, etc.)
                    decimals: int representing number of decimals for token
        """
        if chain not in Web3Query.supportedChains:
            raise KeyError(f"RPC for chain {chain} not supported!")
        # look for cached result
        try:
            return Web3Query._chainAddrToSymbolDecimalsCache[chain][addr]
        except KeyError:
            pass  # has not yet been cached
        _contract = w3["ETH"].eth.contract(
            address=Web3.toChecksumAddress(addr),
            abi=ERC20_ABI)
        _return = (
            _contract.functions.symbol().call(),
            _contract.functions.decimals().call())
        # cache the result
        Web3Query._chainAddrToSymbolDecimalsCache[chain][addr] = _return
        return _return

    @staticmethod
    def get_block_datetime(block_hash: str, chain: str):
        # NOTE: currently doesn't account for daylight savings time well
        timestamp = w3[chain].eth.get_block(block_hash)["timestamp"]
        utc_offset = time.localtime().tm_gmtoff / 3600
        dt_utc = datetime.datetime.fromtimestamp(timestamp) #  , tz=pytz.utc)
        dt_local = dt_utc - datetime.timedelta(hours=utc_offset)
        return dt_local.strftime("%m/%d/%Y %I:%M:%S %p")

    @staticmethod
    def get_swap_summary(tx_hash: str, exchange: Exchange):
        """
        This function tries to return a swap tx's summary given a tx_hash
        :param tx_hash: str hash of tx to retrieve
        :param exchange: Exchange which tx performed a swap on
        :return: tbd
        """
        try:
            # transaction
            _tx = w3[exchange.chain].eth.get_transaction(tx_hash)
            # receipt for logs and block (for time)
            _tx_receipt = w3[exchange.chain].eth.get_transaction_receipt(tx_hash)
            if _tx_receipt["status"] == 0:
                print(f"WARNING: tx {tx_hash} was reverted by EVM, skipping...")
                return None
            _logs = _tx_receipt.logs
            _date_time = Web3Query.get_block_datetime(_tx_receipt.blockHash, exchange.chain)
            if exchange.name == "sushiswap" and exchange.chain == "ETH" and exchange.method == "Swap ETH For Exact Tokens":
                _amount_eth = _logs[0]["data"]
                _amount_eth = int(_amount_eth, 16) / 1e18
                _eth_price = float(SubgraphQuery.get_eth_price_at_block(_tx_receipt.blockNumber))
                _total_eth_usd = _amount_eth * _eth_price
                # token addr is arg 3 of 4, prepend w 0x
                _token_addr = "0x" + _tx["input"][-40:]
                # get token symbol and decimals
                _token_symbol, _token_decimals = Web3Query.get_token_symbol_and_decimals(_token_addr, exchange.chain)
                _amount_token = int("0x" + _logs[-1]["data"][2+64*2:2+64*3], 16) / (pow(10, _token_decimals))
                swap_summary = SwapSummary(
                    sent=TokenAmount("ETH", "0x0", _amount_eth, _eth_price, _total_eth_usd),
                    received=TokenAmount(_token_symbol, _token_addr, _amount_token, "", "equal"),
                    book_fee_with="buy",
                    fee_chain=exchange.chain,
                    tx_hash=tx_hash,
                    date_time=_date_time
                )
            if exchange.name == "sushiswap" and exchange.chain == "ETH" and exchange.method == "Swap Exact Tokens For ETH":
                # token addr is address of log 0
                _token_addr = _logs[0]["address"]
                # get token symbol and decimals
                _token_symbol, _token_decimals = Web3Query.get_token_symbol_and_decimals(_token_addr, exchange.chain)
                _amount_token = int(_logs[0]["data"], 16) / (pow(10, _token_decimals))
                # get received eth amount and calc usd values
                _amount_eth = int(_logs[-1]["data"], 16) / 1e18
                _eth_price = float(SubgraphQuery.get_eth_price_at_block(_tx_receipt.blockNumber))
                _total_eth_usd = _amount_eth * _eth_price
                swap_summary = SwapSummary(
                    sent=TokenAmount(_token_symbol, _token_addr, _amount_token, "", "equal"),
                    received=TokenAmount("ETH", "0x0", _amount_eth, _eth_price, _total_eth_usd),
                    book_fee_with="sell",
                    fee_chain=exchange.chain,
                    tx_hash=tx_hash,
                    date_time=_date_time
                )
            return swap_summary
        except ValueError as e:
            print(f"Error while getting tx summary for tx:: {tx_hash}. \n" +
                  "Ensure tx is a valid swap on a valid exchange. \n")
            raise e
        return None

    @staticmethod
    def get_punk_summary(tx_hash: str, method: str):
        """
        Returns a PunkSummary instance that gives additional info
        about punk id and value of ether for txs interacting with
        the ETH cryptopunks market.
        :param tx_hash: str hash of tx to be examined
        :param method: str Method called in cryptopunks market.
                       currently supported methods are:
                         - "Offer Punk For Sale"
                         - "Offer Punk For Sale To Address"
        :return: PunkSummary
        """
        try:
            # transaction
            # _tx = w3["ETH"].eth.get_transaction(tx_hash)
            # receipt for logs
            _tx_receipt = w3["ETH"].eth.get_transaction_receipt(tx_hash)
            if _tx_receipt["status"] == 0:
                print(f"WARNING: tx {tx_hash} was reverted by EVM, skipping...")
                return None
            _logs = _tx_receipt.logs
            if method == "Offer Punk For Sale" or method == "Offer Punk For Sale To Address":
                val_eth = int(_logs[0]["data"], 16) / 1e18
                punk_id = int.from_bytes(_logs[0]['topics'][1], "big")
                _to_address = ""
                if method == "Offer Punk For Sale To Address":
                    _to_address = '0x' + _logs[0]['topics'][2].hex()[-40:]
                punk_summary = PunkSummary(
                    tx_hash=tx_hash,
                    punk_id=punk_id,
                    val_eth=val_eth,
                    to_address=_to_address
                )
            return punk_summary
        except ValueError as e:
            print(f"Error while getting punk summary for tx:: {tx_hash}. \n" +
                  f"Ensure tx method, {method}, is a supported interaction with punks contract. \n")
            raise e
        except UnboundLocalError as e:
            print(f"Ensure tx method, {method}, is a supported interaction with punks contract.")
        return None

