# OpenCryptoTax
Free, open source software to potentially help crypto users 
when preparing their taxes.
>Absolutely NO guarantee of accuracy is included with this software or documentation.
>
>Absolutely NO Tax or financial advice is included in this software or documentation.
>
>Absolutely NO information that this software gives as examples of tax calculation to help comply with US or any other country's
>tax laws is shall be considered tax or financial advice whatsoever.
>
TLDR: Discuss everything with your accountant and don't trust this software to do anything.

### USE AT YOUR OWN RISK!

## Overview
This repository is a custom software solution used to help track/document/define
relevant parameters related to taxes owed on assets such as cryptocurrency.

## Assumptions
FIFO rules are used. Details such as properly including fees in basis
prices, "selling" assets used to pay fees (e.g. pay gas fees in ETH) are
all intended to be properly followed.

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

### TODO Generate TokenTax Summary
```buildoutcfg
python generate_tokentax_summary.py ./input/input_valid.csv
```
This command will turn a valid input file into a CSV compatible with TokenTax.

TokenTax CSV specs are defined here: https://help.tokentax.co/en/articles/1707630-create-a-manual-csv-report-of-your-transactions

This is the file you would want to send to your accountant, or use with TokenTax directly.

The following is a list of likely "Type" categorization based on TokenTax's spec.
**NONE OF THIS IS TAX ADVICE OR FINANCIAL ADVICE**

| Condition / situation | TokenTax Type |
| ----------------------| ------------- |
| isOrdinaryIncome | Income [0] |
| mining (business) | Trade [1] | 
| swap/buy/sell | Trade |
| gas (to be included in basis) | Totals listed in FeeAmount and FeeCurrency [2] [3] |
| gas-only (not in any basis or trade fee) | Spend [4] |
| gift (from me to someone else) | Gift [5] |
| gift (to me from someone else) | Trade [6] |

>[0] includes events such as airdrops, hard forks, hobby mining, staking rewards, claimable LP rewards
>
>[1] business income tracked elsewhere, but personally treat as buying mined currency with USD
>
>[2] if multiple fee currencies (e.g. ETH and USD), include USD in basis, making sure to track any asset sales used to pay for gas (e.g. pay ethereum gas fees in ETH *must* be tracked as sale of ETH) 
>
>[3] any relevant tx_hash(es) should be listed in comment json { "feeTxHashes": string[] }
>
>[4] spend amount = 0, track gas fees in FeeAmount & FeeCurrency. if multiple currencies, require to be broken up.
>
>[5] leave buy blank, use sell fields, set exchange as "Gift"
>
>[6] my understanding is that Buy would be gift-giver's cost basis :)
>
>
>

## TODO Generate TokenTax Summary + Current Balances
```buildoutcfg
python generate_tokentax_summary_with_balances.py ./input/input_valid.csv
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