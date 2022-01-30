import pandas as pd
import numpy as np
from pathlib import Path


NUM_GAS_TX_ALLOWED = 14


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
                date = row["Date"]
                # sells
                sell_asset = row["SellAsset"]
                sell_qty = row["SellQty"]
                sell_spot_price_usd = row["SellSpotPriceUSD"]
                sell_total_usd = row["SellTotalUSD"]
                # buys
                buy_asset = row["BuyAsset"]
                buy_qty = row["BuyQty"]
                buy_spot_price_usd = row["BuySpotPriceUSD"]
                buy_total_usd = row["BuyTotalUSD"]
                # fees
                book_fee_with = row["BookFeeWith"]
                fee_chain = [0]
                fee_tx = [0]
                fee_tx_gas_asset_price_override = [0]
                for i in range(0, NUM_GAS_TX_ALLOWED):
                    fee_chain.append(row[f"FeeChain{i+1}"])
                    fee_tx.append(row[f"FeeTx{i+1}"])
                    fee_tx_gas_asset_price_override.append(row[f"FeeTx{i+1}GasAssetPriceOverride"])
                # TODO aux fee assets currently not supported
                aux_fee_asset = row["AuxFeeAsset"]
                aux_fee_qty = row["AuxFeeQty"]
                aux_fee_spot_price = row["AuxFeeSpotPrice"]
                # USD fee
                aux_usd_fee = row["AuxUSDFee"]
                # Gifts
                is_gift_from_me = row["IsGiftFromMe"]
                is_gift_to_me = row["IsGiftToMe"]
                aux_gift_basis = row["GiftBasis"]
                # Income types
                is_ordinary_income = row["IsOrdinaryIncome"]
                is_business_income_1 = row["IsBusinessIncome1"]
                is_business_income_2 = row["IsBusinessIncome2"]
                # metadata
                other_tx_receipts = row["Other Tx Receipts (fees not auto-calculated or included)"]
                purchased_from = row["Purchased From"]
                other_notes = row["Other Notes"]

                # skip row if nothing happened
                if pd.isnull(date) and pd.isnull(buy_asset) and pd.isnull(sell_asset) and pd.isnull(fee_tx[1]):
                    print(f"[WARNING] skipped empty line: {line}")
                    continue
                # ensure minimum required fields
                if pd.isnull(date):
                    raise LookupError(f"[ERROR] missing date on line {line}")
                if pd.isnull(sell_asset) and pd.isnull(buy_asset) and pd.isnull(fee_tx[1]):
                    raise LookupError(f"[ERROR] no buy/sell/gas data for line {line}")
                # validate book fee with
                if not pd.isnull(book_fee_with) and book_fee_with not in ["sell", "buy", "gas"]:
                    raise ValueError(f"[ERROR] non-null BookFeeWith must be 'buy', 'sell', or 'gas' on line {line}")
                if book_fee_with == "gas":
                    if not pd.isnull(sell_asset) or not pd.isnull(buy_asset):
                        raise ValueError(f"[ERROR] BookFeeWith is 'gas', but sell/buy data exists on line {line}")
                # continue checking minimum required fields
                if pd.isnull(sell_asset) and pd.isnull(buy_asset):
                    # must be a gas
                    if (book_fee_with != "gas") or pd.isnull(fee_tx[1]):
                        raise LookupError(f"[ERROR] no buy/sell & no gas data for line {line}")
                elif pd.isnull(sell_asset) and not pd.isnull(buy_asset):
                    # must be a buy
                    if (book_fee_with != "buy"):
                        book_fee_with = "buy"
                else:
                    # must be a sell
                    if (book_fee_with != "sell"):
                        book_fee_with = "sell"
                # fully populate sell/buy spot price and/or total prices
                if not pd.isnull(sell_asset) and not pd.isnull(buy_asset):
                    # swap
                    # if either is equal, set equal to other's total
                    if sell_total_usd == "equal":
                        if pd.isnull(buy_total_usd) or buy_total_usd == "equal":
                            if pd.isnull(buy_spot_price_usd):
                                raise LookupError(f"[ERROR] price not fully defined for line {line}")
                            buy_total_usd = buy_qty * buy_spot_price_usd
                        sell_total_usd = buy_total_usd
                        # ensure sell is not over-defined
                        if not pd.isnull(sell_spot_price_usd):
                            raise LookupError(f"[ERROR] sell spot price over-defines line {line}")
                        # we can over-define at this point by calculating
                        sell_spot_price_usd = sell_total_usd / sell_qty
                    elif buy_total_usd == "equal":
                        if pd.isnull(sell_total_usd):
                            if pd.isnull(sell_spot_price_usd):
                                raise LookupError(f"[ERROR] price not fully defined for line {line}")
                            sell_total_usd = sell_qty * sell_spot_price_usd
                        buy_total_usd = sell_total_usd
                        # ensure buy is not over-defined
                        if not pd.isnull(buy_spot_price_usd):
                            raise LookupError(f"[ERROR] buy spot price over-defines line {line}")
                        # we can over-define at this point by calculating
                        buy_spot_price_usd = buy_total_usd / buy_qty
                    # guaranteed totals are filled in, ensure spot-prices are calculated
                    if pd.isnull(buy_spot_price_usd):
                        buy_spot_price_usd = buy_total_usd / buy_qty
                    if pd.isnull(sell_spot_price_usd):
                        sell_spot_price_usd = sell_total_usd / sell_qty
                    # end swap
                # no "equal"s, so ensure if not null, sell/buy are fully filled in
                if not pd.isnull(sell_asset):
                    if pd.isnull(sell_total_usd):
                        sell_total_usd = sell_qty * sell_spot_price_usd
                    if pd.isnull(sell_spot_price_usd):
                        sell_spot_price_usd = sell_total_usd / sell_qty
                if not pd.isnull(buy_asset):
                    if pd.isnull(buy_total_usd):
                        buy_total_usd = buy_qty * buy_spot_price_usd
                    if pd.isnull(buy_spot_price_usd):
                        buy_spot_price_usd = buy_total_usd / buy_qty
                # ensure we define where to book fees if a swap
                if not pd.isnull(sell_asset) and not pd.isnull(buy_asset):
                    # swap
                    if pd.isnull(book_fee_with):
                        raise LookupError(f"BookFeeWith must be defined for swap on line {line}")
                # if no FeeChain defined for *any* FeeTx, fill it with ETH by default
                for i in range(0, NUM_GAS_TX_ALLOWED):
                    if not pd.isnull(fee_tx[i+1]):
                        if pd.isnull(fee_chain[i+1]):
                            fee_chain[i+1] = "ETH"
                # update df row to new values
                self.df.loc[index, "Date"] = date
                # sells
                self.df.loc[index, "SellAsset"] = sell_asset
                self.df.loc[index, "SellQty"] = sell_qty
                self.df.loc[index, "SellSpotPriceUSD"] = sell_spot_price_usd
                self.df.loc[index, "SellTotalUSD"] = sell_total_usd
                # buys
                self.df.loc[index, "BuyAsset"] = buy_asset
                self.df.loc[index, "BuyQty"] = buy_qty
                self.df.loc[index, "BuySpotPriceUSD"] = buy_spot_price_usd
                self.df.loc[index, "BuyTotalUSD"] = buy_total_usd
                # fees
                self.df.loc[index, "BookFeeWith"] = book_fee_with
                for i in range(0, NUM_GAS_TX_ALLOWED):
                    self.df.loc[index, f"FeeChain{i+1}"] = fee_chain[i+1]
                    self.df.loc[index, f"FeeTx{i+1}"] = fee_tx[i+1]
                    self.df.loc[index, f"FeeTx{i+1}GasAssetPriceOverride"] = fee_tx_gas_asset_price_override[i+1]
                # TODO aux fee assets currently not supported
                self.df.loc[index, "AuxFeeAsset"] = aux_fee_asset
                self.df.loc[index, "AuxFeeQty"] = aux_fee_qty
                self.df.loc[index, "AuxFeeSpotPrice"] = aux_fee_spot_price
                # USD fee
                self.df.loc[index, "AuxUSDFee"] = aux_usd_fee
                # Gifts
                self.df.loc[index, "IsGiftFromMe"] = is_gift_from_me
                self.df.loc[index, "IsGiftToMe"] = is_gift_to_me
                self.df.loc[index, "GiftBasis"] = aux_gift_basis
                # Income types
                self.df.loc[index, "IsOrdinaryIncome"] = is_ordinary_income
                self.df.loc[index, "IsBusinessIncome1"] = is_business_income_1
                self.df.loc[index, "IsBusinessIncome2"] = is_business_income_2
                # metadata
                self.df.loc[index, "Other Tx Receipts (fees not auto-calculated or included)"] = other_tx_receipts
                self.df.loc[index, "Purchased From"] = purchased_from
                self.df.loc[index, "Other Notes"] = other_notes
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

    def __init__(self, input_valid: Path, print_preview: bool = False):
        # load input file
        self.df = pd.read_csv(input_valid, engine='python')
        if print_preview:
            print(self.df)
        pass

    def process(self):
        """
        This processes loaded input data (looks up all fee tx, builds entire buy/sell basis sheet)
        """
        pass

    def generate_tokentax_summary(self, output_file: Path):
        """
        This generates a TokenTax csv output file
        :param output_file: Path TokenTax output file
        """
        pass
