import pandas as pd


COLUMN_RENAME_MAP = {
    "Product Name": "product_name",
    "Type": "product_type",
    "Quantity": "quantity",
    "Gross Amount": "gross_amount",
    "Discounts": "discounts",
    "Collab %": "collab_amount",
    "BeatStars %": "beatstars_fee",
    "Net": "net_revenue",
}


def clean_beatstars_sales(beatstars_sales_df):
    """
    Clean and standardise the raw BeatStars sales report.

    Args:
        beatstars_sales_df: Raw DataFrame from the BeatStars CSV.

    Returns:
        A cleaned Silver-layer DataFrame.
    """

    beatstars_sales_df = beatstars_sales_df.copy()

    beatstars_sales_df = beatstars_sales_df.rename(
        columns=COLUMN_RENAME_MAP
    )

    text_columns = [
        "product_name",
        "product_type",
    ]

    numeric_columns = [
        "quantity",
        "gross_amount",
        "discounts",
        "collab_amount",
        "beatstars_fee",
        "net_revenue",
    ]

    for column in text_columns:
        beatstars_sales_df[column] = (
            beatstars_sales_df[column]
            .astype("string")
            .str.strip()
        )

    for column in numeric_columns:
        beatstars_sales_df[column] = pd.to_numeric(
            beatstars_sales_df[column],
            errors="coerce",
        )

    beatstars_sales_df = beatstars_sales_df.dropna(
        subset=["product_name"]
    )

    beatstars_sales_df = beatstars_sales_df.reset_index(drop=True)

    return beatstars_sales_df


def validate_beatstars_sales(beatstars_sales_df):
    """
    Print a basic data-quality report for BeatStars sales data.
    """

    print("\n--- BeatStars data quality report ---")

    print(f"Rows: {len(beatstars_sales_df)}")
    print(f"Columns: {len(beatstars_sales_df.columns)}")

    print("\nMissing values:")
    print(beatstars_sales_df.isna().sum())

    print("\nData types:")
    print(beatstars_sales_df.dtypes)

    print("\nProduct types:")
    print(beatstars_sales_df["product_type"].value_counts(dropna=False))

    print("--- End of report ---\n")