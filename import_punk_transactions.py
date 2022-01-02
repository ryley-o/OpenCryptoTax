from web3_api import Web3Query, Exchange, SwapSummary, PunkSummary
import pandas as pd

df = pd.read_csv(r'input/utils/import_punk_txs.csv', engine='python')
df_out = pd.DataFrame(columns=PunkSummary.col_headers())


for index, row in df.iterrows():
    _tx = row['tx']
    _method=row['method']
    _punk_summary = Web3Query.get_punk_summary(_tx, _method)
    df_out.loc[len(df_out.index)] = _punk_summary.export_row()

_out_dir = r'out/utils/exported_punk_txs.csv'
df_out.to_csv(_out_dir)
print(f'Exported tx summary file: {_out_dir}')

