import pandas as pd

df = pd.read_parquet(
    "data/silver/beatstars/sales_summary.parquet"
)

print(df)