from pathlib import Path

import pandas as pd
from google.cloud import bigquery

from src.load.bigquery import load_dataframe_to_bigquery


BEAT_SALES_PATH = Path(
    "data/normalized/fact_beat_sales.parquet"
)

PAYMENT_SPLITS_PATH = Path(
    "data/normalized/fact_payment_splits.parquet"
)


def main() -> None:
    fact_beat_sales_df = pd.read_parquet(
        BEAT_SALES_PATH
    )

    fact_payment_splits_df = pd.read_parquet(
        PAYMENT_SPLITS_PATH
    )

    load_dataframe_to_bigquery(
        dataframe=fact_beat_sales_df,
        table_name="fact_beat_sales",
        write_disposition=(
            bigquery.WriteDisposition.WRITE_TRUNCATE
        ),
    )

    load_dataframe_to_bigquery(
        dataframe=fact_payment_splits_df,
        table_name="fact_payment_splits",
        write_disposition=(
            bigquery.WriteDisposition.WRITE_TRUNCATE
        ),
    )


if __name__ == "__main__":
    main()