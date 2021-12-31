import pandas as pd
from collections import defaultdict
from datetime import datetime, timedelta
from collections import OrderedDict
from copy import deepcopy
import dateparser
from web3_api import Web3Query
from subgraph_api import SubgraphQuery

# # Temporary web3 query examples
# tx_hash = "0xe5e226fe713ff2931dc609601d013e04df5a9cdced0ee5b6a0d4e12f3fd4e610"
# print(Web3Query.get_tx_fee(tx_hash, "ETH"))
# tx_hash = "0x779b908460007c33e94cadf31d6d9f1aa25064c4135f0d3f524ceb74f1e267d6"
# print(Web3Query.get_tx_fee(tx_hash, "BSC"))
# # Temporary subgraph_api query examples
# print(SubgraphQuery.get_eth_price_at_block(13708355))
# print(SubgraphQuery.get_bnb_price_at_bsc_block(13736082))
#
# exit()

LONG_TERM_CAP_GAIN_RATE_EST = 0.15  # estimate
SHORT_TERM_CAP_GAIN_RATE_EST = 0.22  # estimate


class Action:

    def __init__(self, id, tx_type, qty_change, spot_price, fees_asset_sym, fees_asset, fees_usd, receipts, purchase_info, meta):
        self.id = id
        self.tx_type = tx_type
        self.qty_change = float(qty_change)
        self.spot_price = float(spot_price)
        self.fees_asset_sym = fees_asset_sym
        self.fees_asset = float(fees_asset)
        self.fees_usd = float(fees_usd)
        self.receipts = receipts
        self.purchase_info = purchase_info
        self.meta = meta
        # calculated properties
        self.action = "buy"
        if qty_change < 0:
            self.action = "sell"
        if qty_change == 0:
            self.basis_total_usd = 0
            self.basis_price = 0
        elif self.action == "buy":
            # calculate basis
            self.basis_total_usd = self.spot_price * self.qty_change + self.fees_usd
            self.basis_price = float(self.basis_total_usd) / float(self.qty_change)
        if self.action == "sell":
            # calculate sale price, minus fees
            self.sale_actual_revenue_usd = self.spot_price * self.qty_change - self.fees_usd
            self.sale_actual_price = float(self.sale_actual_revenue_usd) / float(self.qty_change)
        # calculate income if an income
        self.income_non_business = "-"
        if self.tx_type.lower() == 'income_non_business':
            # note: cannot subtract fees here, since get to include fees in basis. otherwise would be double tax benefit
            self.income_non_business = self.spot_price * self.qty_change
        # Important error checking
        if self.action == "buy" and self.tx_type == "Sell":
            raise ValueError(f"QtyChange {self.qty_change}: "
                             f"Identified a Tx Type Sell that has a positive or zero amount-change value. ERROR!")


class Buy:

    def __init__(self, action: Action, date):
        self.action = action
        self.date = date
        self.basis_remaining = deepcopy(self.action.qty_change)
        self.sell_ids_lt = []
        self.sell_ids_st = []

class Sell:

    def __init__(self, action: Action, date):
        self.action = action
        self.date = date
        self.sell_qty_remaining = -1.0 * deepcopy(self.action.qty_change)
        self.basis_total_cost = 0
        self.basis_total_qty_lt = 0
        self.basis_total_cost_lt = 0
        self.basis_total_qty_st = 0
        self.basis_total_cost_st = 0
        self.buy_ids_lt = []
        self.buy_ids_st = []
        self.cap_gain_lt = None
        self.cap_gain_st = None
        self.cap_gain = None
        self.cap_gain_tax_est_lt = None
        self.cap_gain_tax_est_st = None
        self.cap_gain_tax_est = None


df = pd.read_csv(r'input.csv', engine='python')
print(df)

assets = defaultdict(dict)
# build asset dictionary
ind = 0.0
for index, row in df.iterrows():
    _asset = row['Asset']
    # build an event for what happened on this date
    _date = dateparser.parse(row['Date'])
    if _date in assets[_asset]:
        raise KeyError(f"Duplicate datetimes. please remove duplicate datetime {_date} to ensure proper ordering of fifo")
    val = Action(ind, row['Type'], row['Qty Change'], row['Spot Price USD'], row['TxnFeeAsset'], row['TxnFee(ASSET)'], row['TxnFee(USD)'],
                 row['Tx Receipts'], row['Purchased From'], row['Other'])
    assets[_asset][_date] = val
    ind += 1.0

# treat every transaction gas fee is paid in <gas fee asset>, and is essentially a small sale of <gas fee asset>
# for usd to pay gas
# add sales 1 second after each tx to calculate gains or loss on the <gas fee asset> sold to pay gas fees
# this applies to both buys and sells, any tx that has a gas fee
try:
    for _asset in assets.keys():
        dates = sorted(assets[_asset].keys())
        for date in dates:
            # add a new sell event that has no fees, but tracks the "sale" of eth used to pay for this tx gas fee
            action = assets[_asset][date]
            if action.fees_asset <= 0:
                # no gas fees with this action, so no need to add a gas fee "sale" tx
                continue
            gas_date = date + timedelta(seconds=1)
            if gas_date in assets[_asset]:
                raise KeyError(f"Duplicate datetimes for a gas_date. please remove duplicate datetime {gas_date} to ensure proper ordering of fifo")
            _spot_price = action.fees_usd / action.fees_asset
            _qty_change = -1.0 * action.fees_asset
            assets[action.fees_asset_sym][gas_date] = Action(action.id + 0.1, 'fee', _qty_change, _spot_price, '', 0.0, 0.0,
                                                             action.receipts, action.purchase_info, 'FEE PAYMENT')
except RuntimeError as e:
    Warning("Did you pay a gas fee using an asset you did not previously add a buy for?")
    raise e

# generate sorted list of buys and sells
buys = dict()
sells = dict()
for _asset in assets.keys():
    buys[_asset] = []
    sells[_asset] = []
    # get ordered list of keys
    dates = sorted(assets[_asset].keys())
    # step through each date, make a list of buys only
    for date in dates:
        if assets[_asset][date].action == 'buy':
            buys[_asset].append(Buy(assets[_asset][date], date))
        elif assets[_asset][date].action == 'sell':
            sells[_asset].append(Sell(assets[_asset][date], date))

# for each sell, calculate basis, gains, etc.
for _asset in assets.keys():
    for sell in sells[_asset]:
        # build up basis while still sell_qty_remaining
        for buy in buys[_asset]:
            if sell.sell_qty_remaining <= 0:
                if sell.sell_qty_remaining < 0:
                    raise ValueError('Sell qty remaining less than zero, should never happen!')
                break
            if buy.basis_remaining == 0:
                continue
            # subtract the appropriate amount of basis qty
            basis_qty = min(buy.basis_remaining, sell.sell_qty_remaining)
            buy.basis_remaining -= basis_qty
            sell.sell_qty_remaining -= basis_qty
            # add basis this basis cost to sell's total basis cost
            # must track short and long term separately
            is_lt = (buy.date + timedelta(days=365) < sell.date)
            # sell.basis_total_cost += buy.action.basis_price * basis_qty
            if is_lt:
                sell.basis_total_qty_lt += basis_qty
                sell.basis_total_cost_lt += buy.action.basis_price * basis_qty
                # add the sell IDs to the buy and the buy ID to the sell, as LT
                sell.buy_ids_lt.append(buy.action.id)
                buy.sell_ids_lt.append(sell.action.id)
            else:
                sell.basis_total_qty_st += basis_qty
                sell.basis_total_cost_st += buy.action.basis_price * basis_qty
                # add the sell IDs to the buy and the buy ID to the sell, as ST
                sell.buy_ids_st.append(buy.action.id)
                buy.sell_ids_st.append(sell.action.id)
        if sell.sell_qty_remaining > 0:
            raise ValueError(f"Sell ID {sell.action.id} could not find enough buys to complete basis!")
        # calculate short and long term gains for this sell
        sell.cap_gain_lt = (sell.action.sale_actual_price * sell.basis_total_qty_lt) - sell.basis_total_cost_lt
        sell.cap_gain_st = (sell.action.sale_actual_price * sell.basis_total_qty_st) - sell.basis_total_cost_st
        sell.cap_gain = sell.cap_gain_lt + sell.cap_gain_st
        # calculate estimated tax liabilities
        sell.cap_gain_tax_est_lt = sell.cap_gain_lt * LONG_TERM_CAP_GAIN_RATE_EST
        sell.cap_gain_tax_est_st = sell.cap_gain_st * SHORT_TERM_CAP_GAIN_RATE_EST
        sell.cap_gain_tax_est = sell.cap_gain_tax_est_lt + sell.cap_gain_tax_est_st

# Generate capital gains report
# one row per buy/sell
rows = []
for _asset in assets.keys():
    for buy in buys[_asset]:
        row = []
        row.append(buy.action.id)
        row.append(buy.action.tx_type)
        row.append(buy.action.action)
        row.append(buy.date)
        row.append(_asset)
        row.append(buy.action.qty_change)
        row.append(buy.action.spot_price)
        row.append(buy.action.fees_asset_sym)
        row.append(buy.action.fees_asset)
        row.append(buy.action.fees_usd)
        row.append(buy.sell_ids_st)
        row.append(buy.sell_ids_lt)
        row.append(None)
        row.append(None)
        row.append(None)
        row.append(None)
        row.append(None)
        row.append(None)
        row.append(None)
        row.append(None)
        row.append(None)
        row.append(None)
        row.append(buy.action.income_non_business)
        row.append(buy.action.receipts)
        row.append(buy.action.purchase_info)
        row.append(buy.action.meta)
        rows.append(row)
    for sell in sells[_asset]:
        row = []
        row.append(sell.action.id)
        row.append(sell.action.tx_type)
        row.append(sell.action.action)
        row.append(sell.date)
        row.append(_asset)
        row.append(sell.action.qty_change)
        row.append(sell.action.spot_price)
        row.append(sell.action.fees_asset_sym)
        row.append(sell.action.fees_asset)
        row.append(sell.action.fees_usd)
        row.append(sell.buy_ids_st)
        row.append(sell.buy_ids_lt)
        row.append(sell.basis_total_qty_st)
        row.append(sell.basis_total_cost_st)
        row.append(sell.cap_gain_st)
        row.append(sell.cap_gain_tax_est_st)
        row.append(sell.basis_total_qty_lt)
        row.append(sell.basis_total_cost_lt)
        row.append(sell.cap_gain_lt)
        row.append(sell.cap_gain_tax_est_lt)
        row.append(sell.cap_gain)
        row.append(sell.cap_gain_tax_est)
        row.append(sell.action.income_non_business)
        row.append(sell.action.receipts)
        row.append(sell.action.purchase_info)
        row.append(sell.action.meta)
        rows.append(row)

# label dataframe titles
df_titles = ['ID', 'Type', 'Class', 'Date', 'Asset', 'Qty Change', 'Spot Price', 'Fees Asset', 'Fees Qty', 'Fees USD',
             'Buy/Sell IDs ST', 'Buy/Sell IDs LT',
             'Basis Amount ST', 'Basis Cost ST', 'Cap Gain ST', 'Cap Gain Tax Est ST',
             'Basis Amount LT', 'Basis Cost LT', 'Cap Gain LT', 'Cap Gain Tax Est LT',
             'Cap Gain TOT', 'Cap Gain Tax Est TOT',
             'Income_non_business',
             'Receipts', 'Purchase Info', 'Metadata']

report = pd.DataFrame(rows, columns=df_titles)

# sort by date
report_sorted = report.sort_values(by='Date')

# output summary report
print(report_sorted)
report_sorted.to_csv('out.csv')
# html report
html = report_sorted.to_html()
text_file = open("out.html", "w")
text_file.write(html)
text_file.close()

