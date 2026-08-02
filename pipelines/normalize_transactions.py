from pathlib import Path
from datetime import datetime

import pandas as pd


def normalize_column_names(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Return a copy with normalized column names.
    """

    normalized_df = dataframe.copy()

    normalized_df.columns = (
        normalized_df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )

    return normalized_df


def parse_order_timestamp(
    timestamp: str,
):
    """
    Convert a BeatStars timestamp string to datetime.
    """

    if pd.isna(timestamp):
        return pd.NaT

    weekdays = [
        " Monday,",
        " Tuesday,",
        " Wednesday,",
        " Thursday,",
        " Friday,",
        " Saturday,",
        " Sunday,",
    ]

    cleaned_timestamp = timestamp

    for weekday in weekdays:
        cleaned_timestamp = cleaned_timestamp.replace(
            weekday,
            "",
        )

    cleaned_timestamp = (
        cleaned_timestamp
        .replace(" EDT", "")
        .replace(" EST", "")
    )

    return datetime.strptime(
        cleaned_timestamp,
        "%B %d, %Y %I:%M:%S %p",
    )


def parse_transaction_rows(
    transactions_df: pd.DataFrame,
) -> tuple[list[dict], list[dict]]:
    """
    Parse the hierarchical BeatStars export into
    raw beat-sale rows and payment-split rows.
    """

    beat_sales_rows = []
    payment_split_rows = []

    current_invoice = None
    current_order_timestamp_raw = None
    current_item_sequence = 0
    current_order_item_id = None

    for row in transactions_df.itertuples(index=False):
        if pd.notna(row.invoice_number):
            current_invoice = row.invoice_number
            current_item_sequence = 0

        if pd.notna(row.date):
            current_order_timestamp_raw = row.date

        if pd.notna(row.item_name):
            current_item_sequence += 1

            current_order_item_id = (
                f"{current_invoice}_"
                f"{current_item_sequence}"
            )

            beat_sale = {
                "order_item_id": current_order_item_id,
                "invoice_number": current_invoice,
                "item_sequence": current_item_sequence,
                "order_timestamp_raw": (
                    current_order_timestamp_raw
                ),
                "status": row.status,
                "store_type": row.store_type,
                "beat_name_raw": row.item_name,
                "list_price": row.list_price,
                "discount_amount": row.discount,
                "sale_price": row.sale_price,
            }

            beat_sales_rows.append(
                beat_sale
            )

        if current_order_item_id is None:
            raise ValueError(
                "A payment split was found before any "
                "order item had been identified."
            )

        payment_split = {
            "order_item_id": current_order_item_id,
            "invoice_number": current_invoice,
            "item_sequence": current_item_sequence,
            "split_payment_id": row.split_payment_id,
            "split_payment_type": row.split_payment_type,
            "processing_fee": row.processing_fee,
            "split_payment_amount": (
                row.split_payment_amount
            ),
        }

        payment_split_rows.append(
            payment_split
        )

    return beat_sales_rows, payment_split_rows


def build_fact_beat_sales(
    beat_sales_rows: list[dict],
) -> pd.DataFrame:
    """
    Build the raw beat-sales fact table.
    """

    return pd.DataFrame(
        beat_sales_rows
    )


def build_fact_payment_splits(
    payment_split_rows: list[dict],
) -> pd.DataFrame:
    """
    Build the payment-splits fact table.
    """

    return pd.DataFrame(
        payment_split_rows
    )


def enrich_beat_sales(
    beat_sales_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Add cleaned and analysis-ready fields
    to the beat-sales fact table.
    """

    enriched_df = beat_sales_df.copy()

    enriched_df["beat_name_clean"] = (
        enriched_df["beat_name_raw"]
        .str.replace(
            " (COLLABORATOR)",
            "",
            regex=False,
        )
    )

    enriched_df["order_timestamp"] = (
        enriched_df["order_timestamp_raw"]
        .apply(parse_order_timestamp)
    )

    enriched_df["order_date"] = (
        enriched_df["order_timestamp"]
        .dt.date
    )

    enriched_df["is_free_sale"] = (
        enriched_df["sale_price"] == 0
    )

    enriched_df["is_paid_sale"] = (
        enriched_df["sale_price"] > 0
    )

    return enriched_df


def normalize_transactions(
    transactions_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Normalize the hierarchical BeatStars transactions export.
    """

    normalized_df = normalize_column_names(
        transactions_df
    )

    (
        beat_sales_rows,
        payment_split_rows,
    ) = parse_transaction_rows(
        normalized_df
    )

    fact_beat_sales_df = build_fact_beat_sales(
        beat_sales_rows
    )

    fact_beat_sales_df = enrich_beat_sales(
        fact_beat_sales_df
    )

    fact_payment_splits_df = (
        build_fact_payment_splits(
            payment_split_rows
        )
    )

    return (
        fact_beat_sales_df,
        fact_payment_splits_df,
    )


def print_preview(
    fact_beat_sales_df: pd.DataFrame,
    fact_payment_splits_df: pd.DataFrame,
) -> None:
    """
    Print development previews of both normalized tables.
    """

    print("\nFACT BEAT SALES")
    print("-" * 40)

    print(
        fact_beat_sales_df
        .head(10)
        .to_string(index=False)
    )

    print("\nFACT PAYMENT SPLITS")
    print("-" * 40)

    print(
        fact_payment_splits_df
        .head(10)
        .to_string(index=False)
    )

def write_normalized_tables(
    fact_beat_sales_df: pd.DataFrame,
    fact_payment_splits_df: pd.DataFrame,
) -> None:
    """
    Save normalized fact tables as Parquet files.
    """

    output_dir = Path("data/normalized")

    beat_sales_path = (
        output_dir / "fact_beat_sales.parquet"
    )

    payment_splits_path = (
        output_dir / "fact_payment_splits.parquet"
    )

    fact_beat_sales_df.to_parquet(
        beat_sales_path,
        index=False,
    )

    fact_payment_splits_df.to_parquet(
        payment_splits_path,
        index=False,
    )

    print("\nSaved normalized tables:")
    print(f"- {beat_sales_path}")
    print(f"- {payment_splits_path}")

def main() -> None:
    transactions_df = pd.read_csv(
        "data/transactions/transactions.csv",
        skiprows=2,
    )

    (
    fact_beat_sales_df,
    fact_payment_splits_df,
) = normalize_transactions(
    transactions_df
)

    write_normalized_tables(
        fact_beat_sales_df,
        fact_payment_splits_df,
)

    print_preview(
        fact_beat_sales_df,
        fact_payment_splits_df,
)


if __name__ == "__main__":
    main()