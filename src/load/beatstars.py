from pathlib import Path

import pandas as pd


SILVER_BEATSTARS_PATH = Path(
    "data/silver/beatstars/sales_summary.parquet"
)


def load_beatstars_sales_to_silver(
    beatstars_sales_df: pd.DataFrame,
) -> None:
    """
    Save the cleaned BeatStars sales data
    to the Silver layer.
    """

    SILVER_BEATSTARS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    beatstars_sales_df.to_parquet(
        SILVER_BEATSTARS_PATH,
        index=False,
    )

    print(
        f"\n✅ Silver table saved to:\n{SILVER_BEATSTARS_PATH}"
    )