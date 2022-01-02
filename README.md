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

#### Import Util
A simple import helper util may help with populating the input.csv file.
Currently, running `import_transactions.py` can automatically import (i.e. format)
sushiswap `Swap ETH For Exact Tokens` and `Swap Exact Tokens For ETH`
calls. `input/utils/import_swap_txs.example.csv` provides an example
formatted list of transactions to import. The user must create a file
`input/users/import_swap_txs.csv` to be loaded when running the command:
```
python import_transactions.py
```

### Generate outputs
simply run the following command to generate an out.csv and html file based on 
a populated input file.
```buildoutcfg
TODO
```

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
