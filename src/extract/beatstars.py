from pathlib import Path

import pandas as pd


RAW_SALES_REPORT_PATH = Path(
    "data/raw/beatstars/sales_report.csv"
)


def extract_beatstars_sales():
    """
    Extract BeatStars sales report from the raw CSV file.

    Returns:
        pd.DataFrame
    """

    beatstars_sales_df = pd.read_csv(
        RAW_SALES_REPORT_PATH,
        skiprows=6,
    )

    return beatstars_sales_df