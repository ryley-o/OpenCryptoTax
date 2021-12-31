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
- **[Buy/Sell]SpotPrice/TotalUSD** - Either price of asset or total cost in USD
  must be populated. Both should not be populated, but will prefer 
  spot-price.
- **IsOrdinaryIncome** - Set to `true` or `yes` if `Buy` asset is ordinary income.
  This will treat the value of the received asset (in USD) as ordinary income, 
  and track the asset as "bought" at the appropriate cost basis 
  (`Spot Price` + any fees).
- ***SpotPrice** - Price in USD of qty 1.00 of asset
- **FeeChain[N]** - Chain of tx to get fee info from web, options are `ETH`, `BSC`
- **FeeTx[N]** - tx hash to get fee info from web
- **AuxFeeAsset** - Auxiliary fee paid in some asset defined here
- **FeeUSD** - Any fees paid in USD

### Generate outputs
simply run the following command to generate an out.csv and html file based on 
a populated input file.
```buildoutcfg
yo@
```

## Other

## Helpful Links
The following links references different endpoints/dependencies 
related to this software.
- web3py: https://web3py.readthedocs.io/en/stable/web3.eth.html
- recommended web3 provider: https://getblock.io/
- pancake swap subgraph endpoint explorer: https://bsc.streamingfast.io/subgraphs/name/pancakeswap/exchange-v2/graphql
  - used for historical BNB prices (relative to BUSD)
- uniswap v2 subgraph: https://thegraph.com/hosted-service/subgraph/uniswap/uniswap-v2
  - used for historical ETH prices (relative to USDT)
