from web3_api import Web3Query, Exchange, SwapSummary, PunkSummary
import pandas as pd

df = pd.read_csv(r'input/utils/import_punk_txs.csv', engine='python')
df_out = pd.DataFrame(columns=PunkSummary.col_headers())

num_rows = df.shape[0]
for index, row in df.iterrows():
    print(f"...processing tx {index+1} of {num_rows}")
    _tx = row['tx']
    _method=row['method']
    _punk_summary = Web3Query.get_punk_summary(_tx, _method)
    if _punk_summary is not None:
        df_out.loc[len(df_out.index)] = _punk_summary.export_row()
    else:
        print(f"Skipped Swap tx: {row['tx']}")

_out_dir = r'out/utils/exported_punk_txs.csv'
df_out.to_csv(_out_dir)
print(f'Exported tx summary file: {_out_dir}')

