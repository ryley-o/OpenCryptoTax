import pandas as pd
import numpy as np
from pathlib import Path
from web3_api import Web3Query

NUM_GAS_TX_ALLOWED = 14


# object that represents a valid row of input data
class ValidInputRow:

    def __init__(self, row: pd.Series):
        # date
        self.date = row["Date"]
        # sells
        self.sell_asset = row["SellAsset"]
        self.sell_qty = row["SellQty"]
        self.sell_spot_price_usd = row["SellSpotPriceUSD"]
        self.sell_total_usd = row["SellTotalUSD"]
        # buys
        self.buy_asset = row["BuyAsset"]
        self.buy_qty = row["BuyQty"]
        self.buy_spot_price_usd = row["BuySpotPriceUSD"]
        self.buy_total_usd = row["BuyTotalUSD"]
        # fees
        self.book_fee_with = row["BookFeeWith"]
        self.fee_chain = [0]
        self.fee_tx = [0]
        self.fee_tx_gas_asset_price_override = [0]
        for i in range(0, NUM_GAS_TX_ALLOWED):
            self.fee_chain.append(row[f"FeeChain{i + 1}"])
            self.fee_tx.append(row[f"FeeTx{i + 1}"])
            self.fee_tx_gas_asset_price_override.append(row[f"FeeTx{i + 1}GasAssetPriceOverride"])
        # TODO aux fee assets currently not supported
        self.aux_fee_asset = row["AuxFeeAsset"]
        self.aux_fee_qty = row["AuxFeeQty"]
        self.aux_fee_spot_price = row["AuxFeeSpotPrice"]
        # USD fee
        self.aux_usd_fee = row["AuxUSDFee"]
        # Gifts
        self.is_gift_from_me = row["IsGiftFromMe"]
        self.is_gift_to_me = row["IsGiftToMe"]
        self.aux_gift_basis = row["GiftBasis"]
        # Income types
        self.is_ordinary_income = row["IsOrdinaryIncome"]
        self.is_business_income_1 = row["IsBusinessIncome1"]
        self.is_business_income_2 = row["IsBusinessIncome2"]
        # metadata
        self.other_tx_receipts = row["Other Tx Receipts (fees not auto-calculated or included)"]
        self.purchased_from = row["Purchased From"]
        self.other_notes = row["Other Notes"]

    # @classmethod
    # def from_dict(cls, input_dict: dict):
    #     r = cls()
    #     for key, val in input_dict.items():
    #         setattr(r, key, val)
    #     return r


class Helpers:
    fee_chain_to_fee_currency = dict()
    fee_chain_to_fee_currency["ETH"] = "ETH"
    fee_chain_to_fee_currency["BSC"] = "BNB"

    @staticmethod
    def get_fee_currency_from_fee_chain(fee_chain: str):
        return Helpers.fee_chain_to_fee_currency[fee_chain]

    @staticmethod
    def get_tokentax_array(_type: str, buy_amount: float, buy_currency: str, sell_amount: float, sell_currency: str,
                         fee_amount: float, fee_currency: str, exchange: str, group: str, comment: str, date: str):
        return [type, buy_amount, buy_currency, sell_amount, sell_currency, fee_amount, fee_currency,
                exchange, group, comment, date]


# This class validates an input csv/excel file and generates an
# input_valid.csv file fully populated and able to be summarized.
class Validator:

    def __init__(self, unchecked_input: Path, sheet_name: str = "input", print_preview: bool = False):
        # load input file
        self.df = pd.read_excel(unchecked_input, sheet_name=sheet_name)
        if print_preview:
            print(self.df)

    def process(self, output_filename: Path = None):
        num_rows = self.df.shape[0]
        for index, row in self.df.iterrows():
            try:
                line = index + 2
                # print(f"...processing row {index + 1} of {num_rows}")
                # pull out data
                r = ValidInputRow(row)
                # skip row if nothing happened
                if pd.isnull(r.date) and pd.isnull(r.buy_asset) and pd.isnull(r.sell_asset) and pd.isnull(r.fee_tx[1]):
                    print(f"[WARNING] skipped empty line: {line}")
                    continue
                # ensure minimum required fields
                if pd.isnull(r.date):
                    raise LookupError(f"[ERROR] missing date on line {line}")
                if pd.isnull(r.sell_asset) and pd.isnull(r.buy_asset) and pd.isnull(r.fee_tx[1]):
                    raise LookupError(f"[ERROR] no buy/sell/gas data for line {line}")
                # validate book fee with
                if not pd.isnull(r.book_fee_with) and r.book_fee_with not in ["sell", "buy", "gas"]:
                    raise ValueError(f"[ERROR] non-null BookFeeWith must be 'buy', 'sell', or 'gas' on line {line}")
                if r.book_fee_with == "gas":
                    if not pd.isnull(r.sell_asset) or not pd.isnull(r.buy_asset):
                        raise ValueError(f"[ERROR] BookFeeWith is 'gas', but sell/buy data exists on line {line}")
                # continue checking minimum required fields
                if pd.isnull(r.sell_asset) and pd.isnull(r.buy_asset):
                    # must be a gas
                    if (r.book_fee_with != "gas") or pd.isnull(r.fee_tx[1]):
                        raise LookupError(f"[ERROR] no buy/sell & no gas data for line {line}")
                elif pd.isnull(r.sell_asset) and not pd.isnull(r.buy_asset):
                    # must be a buy
                    if (r.book_fee_with != "buy"):
                        r.book_fee_with = "buy"
                else:
                    # must be a sell
                    if (r.book_fee_with != "sell"):
                        r.book_fee_with = "sell"
                # fully populate sell/buy spot price and/or total prices
                if not pd.isnull(r.sell_asset) and not pd.isnull(r.buy_asset):
                    # swap
                    # if either is equal, set equal to other's total
                    if r.sell_total_usd == "equal":
                        if pd.isnull(r.buy_total_usd) or r.buy_total_usd == "equal":
                            if pd.isnull(r.buy_spot_price_usd):
                                raise LookupError(f"[ERROR] price not fully defined for line {line}")
                            r.buy_total_usd = r.buy_qty * r.buy_spot_price_usd
                        r.sell_total_usd = r.buy_total_usd
                        # ensure sell is not over-defined
                        if not pd.isnull(r.sell_spot_price_usd):
                            raise LookupError(f"[ERROR] sell spot price over-defines line {line}")
                        # we can over-define at this point by calculating
                        r.sell_spot_price_usd = r.sell_total_usd / r.sell_qty
                    elif r.buy_total_usd == "equal":
                        if pd.isnull(r.sell_total_usd):
                            if pd.isnull(r.sell_spot_price_usd):
                                raise LookupError(f"[ERROR] price not fully defined for line {line}")
                            r.sell_total_usd = r.sell_qty * r.sell_spot_price_usd
                        r.buy_total_usd = r.sell_total_usd
                        # ensure buy is not over-defined
                        if not pd.isnull(r.buy_spot_price_usd):
                            raise LookupError(f"[ERROR] buy spot price over-defines line {line}")
                        # we can over-define at this point by calculating
                        r.buy_spot_price_usd = r.buy_total_usd / r.buy_qty
                    # guaranteed totals are filled in, ensure spot-prices are calculated
                    if pd.isnull(r.buy_spot_price_usd):
                        r.buy_spot_price_usd = r.buy_total_usd / r.buy_qty
                    if pd.isnull(r.sell_spot_price_usd):
                        r.sell_spot_price_usd = r.sell_total_usd / r.sell_qty
                    # end swap
                # no "equal"s, so ensure if not null, sell/buy are fully filled in
                if not pd.isnull(r.sell_asset):
                    if pd.isnull(r.sell_total_usd):
                        r.sell_total_usd = r.sell_qty * r.sell_spot_price_usd
                    if pd.isnull(r.sell_spot_price_usd):
                        r.sell_spot_price_usd = r.sell_total_usd / r.sell_qty
                if not pd.isnull(r.buy_asset):
                    if pd.isnull(r.buy_total_usd):
                        r.buy_total_usd = r.buy_qty * r.buy_spot_price_usd
                    if pd.isnull(r.buy_spot_price_usd):
                        r.buy_spot_price_usd = r.buy_total_usd / r.buy_qty
                # ensure we define where to book fees if a swap
                if not pd.isnull(r.sell_asset) and not pd.isnull(r.buy_asset):
                    # swap
                    if pd.isnull(r.book_fee_with):
                        raise LookupError(f"BookFeeWith must be defined for swap on line {line}")
                # if no FeeChain defined for *any* FeeTx, fill it with ETH by default
                for i in range(0, NUM_GAS_TX_ALLOWED):
                    if not pd.isnull(r.fee_tx[i+1]):
                        if pd.isnull(r.fee_chain[i+1]):
                            r.fee_chain[i+1] = "ETH"
                # if any fee chain, require every fee for row to be on same chain (otherwise request user to split up)
                _fee_chain = None
                for i in range(0, NUM_GAS_TX_ALLOWED):
                    if not pd.isnull(r.fee_chain[i+1]):
                        if _fee_chain is None:
                            _fee_chain = r.fee_chain[i+1]
                        elif r.fee_chain[i+1] != _fee_chain:
                            raise ValueError(f"Please only book fees in one currency on {line} - split up lines")
                if _fee_chain is not None:
                    # require aux fee and aux USD fees to be null
                    if (not pd.isnull(r.aux_fee_qty)) or (not pd.isnull(r.aux_usd_fee)):
                        raise ValueError(f"Please only book fees in one currency on {line} - aux fees included - split up lines")
                if (not pd.isnull(r.aux_fee_qty)) and (not pd.isnull(r.aux_usd_fee)):
                    raise ValueError(f"Please only book fees in one currency on {line} - aux and usd fee - split up lines")
                # update df row to new values
                self.df.loc[index, "Date"] = r.date
                # sells
                self.df.loc[index, "SellAsset"] = r.sell_asset
                self.df.loc[index, "SellQty"] = r.sell_qty
                self.df.loc[index, "SellSpotPriceUSD"] = r.sell_spot_price_usd
                self.df.loc[index, "SellTotalUSD"] = r.sell_total_usd
                # buys
                self.df.loc[index, "BuyAsset"] = r.buy_asset
                self.df.loc[index, "BuyQty"] = r.buy_qty
                self.df.loc[index, "BuySpotPriceUSD"] = r.buy_spot_price_usd
                self.df.loc[index, "BuyTotalUSD"] = r.buy_total_usd
                # fees
                self.df.loc[index, "BookFeeWith"] = r.book_fee_with
                for i in range(0, NUM_GAS_TX_ALLOWED):
                    self.df.loc[index, f"FeeChain{i+1}"] = r.fee_chain[i+1]
                    self.df.loc[index, f"FeeTx{i+1}"] = r.fee_tx[i+1]
                    self.df.loc[index, f"FeeTx{i+1}GasAssetPriceOverride"] = r.fee_tx_gas_asset_price_override[i+1]
                # TODO aux fee assets currently not supported
                self.df.loc[index, "AuxFeeAsset"] = r.aux_fee_asset
                self.df.loc[index, "AuxFeeQty"] = r.aux_fee_qty
                self.df.loc[index, "AuxFeeSpotPrice"] = r.aux_fee_spot_price
                # USD fee
                self.df.loc[index, "AuxUSDFee"] = r.aux_usd_fee
                # Gifts
                self.df.loc[index, "IsGiftFromMe"] = r.is_gift_from_me
                self.df.loc[index, "IsGiftToMe"] = r.is_gift_to_me
                self.df.loc[index, "GiftBasis"] = r.aux_gift_basis
                # Income types
                self.df.loc[index, "IsOrdinaryIncome"] = r.is_ordinary_income
                self.df.loc[index, "IsBusinessIncome1"] = r.is_business_income_1
                self.df.loc[index, "IsBusinessIncome2"] = r.is_business_income_2
                # metadata
                self.df.loc[index, "Other Tx Receipts (fees not auto-calculated or included)"] = r.other_tx_receipts
                self.df.loc[index, "Purchased From"] = r.purchased_from
                self.df.loc[index, "Other Notes"] = r.other_notes
            except BaseException as err:
                print(f"[ERROR] error while processing line {line}")
                raise
        # save save output
        output_filename = output_filename or Path("input/input_valid.csv")
        self.df.to_csv(output_filename, index=False)
        print(f"[INFO] validated input file generated: {output_filename}")


# This class processes a valid input csv file
# It may generate one of several types of output
class Processor:
    tokentax_columns = [
        "Type",
        "BuyAmount",
        "BuyCurrency",
        "SellAmount",
        "SellCurrency",
        "FeeAmount",
        "FeeCurrency",
        "Exchange",
        "Group",
        "Comment",
        "Date"
    ]

    def __init__(self, input_valid: Path, print_preview: bool = False):
        # load input file
        self.df = pd.read_csv(input_valid, engine='python')
        if print_preview:
            print(self.df)
        pass
        # initialize generic dataframes
        self.df_tt = None  # tokentax formatted dataframe

    @staticmethod
    def safe_get_total_tx_fee_and_currency(r: ValidInputRow):
        # bundle gas tx data
        fee_currency = None
        fee_qty = 0
        for i in range(0, NUM_GAS_TX_ALLOWED):
            _fee_chain = r.fee_chain[i+1]
            _fee_tx = r.fee_tx[i+1]
            _fee_tx_gas_asset_price_override = r.fee_tx_gas_asset_price_override[i+1]
            if not pd.isnull(_fee_chain):
                _fee_currency = Helpers.get_fee_currency_from_fee_chain(_fee_chain)
                if fee_currency is None:
                    # initial value
                    fee_currency = _fee_currency
                elif not fee_currency == _fee_currency:
                    # guard against multiple fee currencies in one line
                    raise ValueError(f"only a single fee_currency allowed in line {line}")
                # add fee qty to total fee qty
                # print(f"[INFO] querying fee data for tx on {_fee_chain}: {_fee_tx}")
                # we NEED a cache system here, 100%
                fee_qty += Web3Query.get_tx_fee(_fee_tx, _fee_chain, False)
        # any usd fees
        if not pd.isnull(r.aux_usd_fee):
            if fee_qty > 0:
                raise ValueError(f"only single fee currency allowed in line {line} - usd and on-chain/aux")
            fee_currency = "USD"
            fee_qty = r.aux_usd_fee
        # any aux fees in different currency
        if not pd.isnull(r.aux_fee_qty):
            if fee_qty > 0:
                raise ValueError(f"only single fee currency allowed in line {line} - usd and on-chain/aux")
            fee_currency = r.aux_fee_asset
            fee_qty = r.aux_fee_qty
        if fee_currency is None:
            fee_currency = ""
        return fee_qty, fee_currency


    def process_tokentax(self):
        """
        This processes loaded input data into a tokentax dataframe
        (looks up all fee tx, builds entire buy/sell basis sheet)
        """
        df_tt = pd.DataFrame(columns=Processor.tokentax_columns)
        num_rows = self.df.shape[0]
        for index, row in self.df.iterrows():
            try:
                line = index + 2
                # pull out data
                r = ValidInputRow(row)
                # every row needs:
                date = r.date
                # translate from row to one or more rows
                # gas - categorize as gas-only, and it is a spend of ether for all gas TXs listed
                if r.book_fee_with == "gas":
                    fee_qty, fee_currency = self.safe_get_total_tx_fee_and_currency(r)
                    # append bundled gas txs to summary
                    if fee_qty == 0:
                        print(f"[WARN] no gas fee transactions found on line {line} - SKIPPED LINE")
                    else:
                        _comment = "gas fees unrelated to buy/sell"
                        df_tt.loc[len(df_tt.index)] = Helpers.get_tokentax_array(_type="Trade",
                                                                                 buy_amount=0,
                                                                                 buy_currency="",
                                                                                 sell_amount=0,
                                                                                 sell_currency="",
                                                                                 fee_amount=fee_qty,
                                                                                 fee_currency=fee_currency,
                                                                                 exchange="",
                                                                                 group="",
                                                                                 comment=_comment,
                                                                                 date=date)
                        # ["Trade", 0, 0, 0, 0, fee_qty, fee_currency, 0, 0, "gas fees unrelated to buy/sell", date]
                # business mining income - treat as a buy on my personal tokentax summary
                if not pd.isnull(r.is_business_income_1):
                    if not (r.is_business_income_1 == 1.0):
                        raise ValueError(f"Unexpected business income 1 for line {line}")
                    # fees should be zero, but check anyway
                    fee_qty, fee_currency = self.safe_get_total_tx_fee_and_currency(r)
                    if not fee_qty == 0:
                        print(f"[WARN] Jellyfish mining income non-zero - is something messed up? line {line}")
                    # append new summary row
                    _comment = "purchased from Jellyfish Mining upon receiving mining rewards. ref ETH tx_hash: " + str(r.other_tx_receipts)
                    df_tt.loc[len(df_tt.index)] = Helpers.get_tokentax_array(_type="Trade",
                                                                             buy_amount=r.buy_qty,
                                                                             buy_currency=r.buy_asset,
                                                                             sell_amount=r.buy_total_usd,
                                                                             sell_currency="USD",
                                                                             fee_amount=fee_qty,
                                                                             fee_currency=fee_currency,
                                                                             exchange="",
                                                                             group="",
                                                                             comment=_comment,
                                                                             date=date)

                #
                # populate row at index
                # df_tt.loc[df_tt.index] = ["Trade", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            except BaseException as err:
                print(f"[ERROR] error while processing line {line}")
                raise
        # save save output
        self.df_tt = df_tt

    def generate_tokentax_summary(self, output_filename: Path = None):
        """
        This generates a TokenTax csv output file
        :param output_filename: Path (optional) TokenTax output file; uses default name if not specified
        """
        # save save output
        output_filename = output_filename or Path("out/summary_tokentax.csv")
        if self.df_tt is None:
            raise LookupError("TokenTax summary not generated - call `process_tokentax` method")
        self.df_tt.to_csv(output_filename, index=False)
        print(f"[INFO] validated input file generated: {output_filename}")
