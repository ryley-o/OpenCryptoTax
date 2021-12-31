from web3 import Web3
from web3.middleware import geth_poa_middleware
import os
from dotenv import load_dotenv
from subgraph_api import SubgraphQuery

EVM_DECIMALS = 1e18  # standard EVM currency has 18 decimals

load_dotenv()  # take environment variables from .env
w3 = dict()
HTTP_PROVIDER_ETH: str = os.environ.get("HTTP_PROVIDER_ETH")
w3["ETH"] = Web3(Web3.HTTPProvider(HTTP_PROVIDER_ETH))
print(f"Current ETH block number: {w3['ETH'].eth.blockNumber}")
HTTP_PROVIDER_BSC: str = os.environ.get("HTTP_PROVIDER_BSC")
w3["BSC"] = Web3(Web3.HTTPProvider(HTTP_PROVIDER_BSC))
# remove POA 32-byte extraData field since BSC is POA w/97 bytes
w3["BSC"].middleware_onion.inject(geth_poa_middleware, layer=0)
print(f"Current BSC block number: {w3['BSC'].eth.blockNumber}")


class Web3Query:

    supportedChains = w3.keys()

    def __init__(self):
        # initialize etherscan web3_api
        self.test = "test"

    @staticmethod
    def get_tx_fee(tx_hash: str, chain: str):
        """
        This function returns tx information given a tx_hash
        :param tx_hash: str hash of tx to retrieve
        :param chain: str indicating which chain to query.
                      supported chains defined in Web3Query.supportedChains
        :return: tbd
        """
        if chain not in Web3Query.supportedChains:
            raise KeyError(f"RPC for chain {chain} not supported!")
        # get gas used
        _tx_receipt = w3[chain].eth.get_transaction_receipt(tx_hash)
        gas_used = _tx_receipt.gasUsed
        gas_price = w3[chain].eth.get_transaction(tx_hash).gasPrice
        # base currency fee
        base_currency_fee = gas_used * gas_price / EVM_DECIMALS
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
        print(gas_asset_price_usd)
        print(base_currency_fee)
        return base_currency_fee * gas_asset_price_usd
