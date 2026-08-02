from pathlib import Path

import pandas as pd


BEAT_SALES_PATH = Path(
    "data/normalized/fact_beat_sales.parquet"
)

PAYMENT_SPLITS_PATH = Path(
    "data/normalized/fact_payment_splits.parquet"
)


def validate_required_columns(
    dataframe: pd.DataFrame,
    required_columns: list[str],
    table_name: str,
) -> None:
    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"{table_name} is missing columns: "
            f"{missing_columns}"
        )

    print(f"✓ {table_name}: required columns exist")


def validate_no_nulls(
    dataframe: pd.DataFrame,
    columns: list[str],
    table_name: str,
) -> None:
    null_counts = dataframe[columns].isna().sum()

    invalid_columns = null_counts[
        null_counts > 0
    ]

    if not invalid_columns.empty:
        raise ValueError(
            f"{table_name} has unexpected nulls:\n"
            f"{invalid_columns}"
        )

    print(f"✓ {table_name}: required fields contain no nulls")


def validate_unique_order_items(
    beat_sales_df: pd.DataFrame,
) -> None:
    duplicate_count = (
        beat_sales_df["order_item_id"]
        .duplicated()
        .sum()
    )

    if duplicate_count > 0:
        raise ValueError(
            f"Found {duplicate_count} duplicate "
            "order_item_id values."
        )

    print("✓ fact_beat_sales: order_item_id is unique")


def validate_split_relationships(
    beat_sales_df: pd.DataFrame,
    payment_splits_df: pd.DataFrame,
) -> None:
    valid_order_item_ids = set(
        beat_sales_df["order_item_id"]
    )

    split_order_item_ids = set(
        payment_splits_df["order_item_id"]
    )

    orphan_ids = (
        split_order_item_ids
        - valid_order_item_ids
    )

    if orphan_ids:
        raise ValueError(
            f"Found payment splits without matching "
            f"beat sales: {len(orphan_ids)}"
        )

    print(
        "✓ fact_payment_splits: all rows match "
        "a beat sale"
    )


def validate_sale_flags(
    beat_sales_df: pd.DataFrame,
) -> None:
    invalid_free_flags = beat_sales_df[
        beat_sales_df["is_free_sale"]
        != (beat_sales_df["sale_price"] == 0)
    ]

    invalid_paid_flags = beat_sales_df[
        beat_sales_df["is_paid_sale"]
        != (beat_sales_df["sale_price"] > 0)
    ]

    if not invalid_free_flags.empty:
        raise ValueError(
            "is_free_sale does not match sale_price."
        )

    if not invalid_paid_flags.empty:
        raise ValueError(
            "is_paid_sale does not match sale_price."
        )

    print("✓ fact_beat_sales: sale flags are valid")


def main() -> None:
    beat_sales_df = pd.read_parquet(
        BEAT_SALES_PATH
    )

    payment_splits_df = pd.read_parquet(
        PAYMENT_SPLITS_PATH
    )

    print("=" * 50)
    print("MAAM TRANSACTION VALIDATION")
    print("=" * 50)

    print(
        f"\nBeat sales rows: "
        f"{len(beat_sales_df)}"
    )

    print(
        f"Payment split rows: "
        f"{len(payment_splits_df)}"
    )

    validate_required_columns(
        beat_sales_df,
        [
            "order_item_id",
            "invoice_number",
            "item_sequence",
            "order_timestamp",
            "beat_name_clean",
            "sale_price",
            "is_free_sale",
            "is_paid_sale",
        ],
        "fact_beat_sales",
    )

    validate_required_columns(
        payment_splits_df,
        [
            "order_item_id",
            "invoice_number",
            "item_sequence",
            "split_payment_id",
            "split_payment_type",
            "split_payment_amount",
        ],
        "fact_payment_splits",
    )

    validate_no_nulls(
        beat_sales_df,
        [
            "order_item_id",
            "invoice_number",
            "item_sequence",
            "order_timestamp",
            "beat_name_clean",
            "sale_price",
        ],
        "fact_beat_sales",
    )

    validate_no_nulls(
        payment_splits_df,
        [
            "order_item_id",
            "invoice_number",
            "item_sequence",
            "split_payment_id",
            "split_payment_type",
            "split_payment_amount",
        ],
        "fact_payment_splits",
    )

    validate_unique_order_items(
        beat_sales_df
    )

    validate_split_relationships(
        beat_sales_df,
        payment_splits_df,
    )

    validate_sale_flags(
        beat_sales_df
    )

    print("\nVALIDATION PASSED ✅")


if __name__ == "__main__":
    main()