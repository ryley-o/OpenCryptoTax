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

### Populate input csv file
`input_RevA.csv` must be filled out. Each row represents a "transaction",
with the understanding that some "transactions" may span multiple blockchain
transactions (e.g. call approve on an ERC20 token, then swap it, all can
be booked as a single "transaction").

Individual rows may include Sell or Buy assets, and define fees.
Details on a few non-intuitive columns:
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

