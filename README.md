# OpenCryptoTax
Free, open source software to potentially help crypto users 
when preparing their taxes.
>Absolutely No Guarantee of accuracy is included with this software.
>Absolutely No Guarantee that software follows US or any other country's
>tax laws is included with this software.

### USE AT YOUR OWN RISK!

## Overview
This repository is a custom software solution used to track/document/define
taxes owed on assets such as cryptocurrency.

## Assumptions
FIFO rules are used. Details such as properly including fees in basis
prices, "selling" assets used to pay fees (e.g. pay gas fees in ETH) are
all properly followed.

## Getting Started

### Environment Variables
Web3 connections are used to pull transaction fee data in this software.
A `.env` file must be created; use `.env.example` as a template. 
Any HTTP RPC provider may be used (GetBlock.io free-tier should suffice).
Currently, ETH and BSC chains are able to be used by this software.

### Populate input csv file
`input_RevA.csv` must be filled out. Each row represents a "transaction",
with the understanding that some "transactions" may span multiple blockchain
transactions (e.g. call approve on an ERC20 token, then swap it, all can
be booked as a single "transaction").

Individual rows may include Sell or Buy assets, and define fees.
Details on a few non-intuitive columns:
- **[Buy/Sell]SpotPrice/TotalUSD** - Either spot price of asset or total cost in USD
  must be populated. Both should not be populated, but will prefer 
  spot-price if both exist. If there is a buy and sell on line, one 
  Buy/Sell `TotalUSD`
  may be set to a special value of `equal` to indicate totals of buy
  and sell should match (preventing double-entry of identical values)
- **IsOrdinaryIncome** - Set to `true` or `yes` if `Buy` asset is ordinary income.
  This will treat the value of the received asset (in USD) as ordinary income, 
  and track the asset as "bought" at the appropriate cost basis 
  (`Spot Price` + any fees).
- ***SpotPrice** - Price in USD of qty 1.00 of asset
- ***BookFeeWith** - (may be blank if only either a buy or sell) Either 
  `blank`, `buy`, `sell`, or `gas`.
  If gas, must be no buy or sell, and will NOT include the fee in any asset cost
  basis or sell fee. Will simply treat as a fee-less sale of ETH for USD, since
  that is all some transactions do (i.e. failed bids, recalled bids, etc.).
- **FeeChain[N]** - Chain of tx to get fee info from web, options are `ETH`, `BSC`
- **FeeTx[N]** - tx hash to get fee info from web
- **AuxFeeAsset** - Auxiliary fee paid in some asset defined here
- **FeeUSD** - Any fees paid in USD

#### Web3/Subgraph helper Utils
**Import Swap Transactions**
```
python import_swap_transactions.py
```

A simple import helper util may help with populating the input.csv file.
Currently, running `import_transactions.py` can automatically import (i.e. format)
sushiswap `Swap ETH For Exact Tokens` and `Swap Exact Tokens For ETH`
calls. `input/utils/import_swap_txs.example.csv` provides an example
formatted list of transactions to import. 

The user must create a file
`input/users/import_swap_txs.csv` to be loaded when running the command.

**Import (Summarize) CryptoPunk Transactions**
```buildoutcfg
python import_punk_transactions.py
```

A simple helper that shows more information about transactions on the CryptoPunks
market for method calls to:
- `Offer Punk For Sale`
  - Exports which punk ID and asking price in ETH
- `Offer Punk For Sale To Address`
  - Exports which punk ID, asking price in ETH, and address offered to

`input/utils/import_punk_txs.example.csv` provides an example
formatted list of transactions to import. 

The user must create a file `input/users/import_punk_txs.csv` to be loaded when running the command.

### Validate input file (generate valid input.csv)
To generate a checked input file `./input/input_valid.csv`:

```buildoutcfg
python generate_valid_input_file.py ./input/<unchecked_input.[csv|xlsx] <xlsx tab name>
// e.g.
python generate_valid_input_file.py input/input.xlsx input
```
> tab name not required
>
> currently, input xlsx files are being used, csv behavior mostly unchecked

Once you have what you think is a valid input.csv/xlsx file, this utility:
- validates the input file
  - expected values are correct formats, qty/spotprice/totals match within tolerance
- generates a new input.csv file that contains all values filled out:
  - shorthand format such as `equal` or whitespace in spot price/total filled in

### TODO Generate Accountant Summary
```buildoutcfg
python generate_accountant_summary.py ./input/input_valid.csv
```
TODO

## TODO Generate Accountant Summary + Current Balances
```buildoutcfg
python generate_accountant_summary_with_balances.py ./input/input_valid.csv
```
TODO


### Generate outputs
simply run the following command to generate an out.csv and html file based on 
a populated input file.
```buildoutcfg
TODO
```


## TODO List
(ALL CODE - YAY!)
- Write code that checks/validates/suggests fixes for input file (maybe excel?)
- Write code that generates tx output summary for accountant input
- Write code that generates above + final balances (for checking, and 
  info that may go into decision making)
- Write code that tracks & outputs tax liability for a given year, given
  tax brackets for that year (not required, but helps quarterly estimates)

## Other

## Helpful Links
The following links references different endpoints/dependencies 
related to this software.
- web3py: https://web3py.readthedocs.io/en/stable/web3.eth.html
- recommended web3 provider: https://getblock.io/
- pancake swap v2 subgraph endpoint explorer: https://bsc.streamingfast.io/subgraphs/name/pancakeswap/exchange-v2/graphql
  - used for historical BNB prices after pancakeswap V2 launch (uses BUSD as proxy for USD)
- pancake swap v1 subgraph endpoint explorer: https://api.thegraph.com/subgraphs/name/ehtec/pancake-subgraph-v1
  - used for historical BNB prices before pancakeswap v2 (uses BUSD as proxy for USD)
- uniswap v2 subgraph: https://thegraph.com/hosted-service/subgraph/uniswap/uniswap-v2
  - used for historical ETH prices (uses USDT as proxy for USD)

## Potentially Helpful Tax Info/References
- **defi lending/borrow/interest (US):** https://cryptotax.io/en-us/defi-taxes-borrowing-lending/