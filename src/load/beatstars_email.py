from datetime import datetime, timezone

from google.cloud import bigquery


PROJECT_ID = "versa-dashboard"
DATASET_ID = "silver"
TABLE_ID = "stg_beatstars_email_sales"


def flatten_sales(sales: list[dict]) -> list[dict]:
    """
    Convert sale-level events into one row per sold item.
    """

    rows = []
    ingested_at = datetime.now(timezone.utc).isoformat()

    for sale in sales:
        for item_sequence, item in enumerate(sale["items"], start=1):
            rows.append(
                {
                    "message_id": sale["message_id"],
                    "invoice_number": sale["invoice_number"],
                    "item_sequence": item_sequence,
                    "sold_at": sale["sold_at"],
                    "source": sale["source"],
                    "total": sale["total"],
                    "beat_title": item["beat_title"],
                    "item_price": item["price"],
                    "license": item["license"],
                    "sale_type": item["sale_type"],
                    "customer_name": sale["customer"]["name"],
                    "customer_email": sale["customer"]["email"],
                    "ingested_at": ingested_at,
                }
            )

    return rows


def load_beatstars_email_sales(sales: list[dict]) -> int:
    """
    Load BeatStars email sales into BigQuery without creating duplicates.

    A unique item is identified by:
    message_id + item_sequence
    """

    rows = flatten_sales(sales)

    if not rows:
        return 0

    client = bigquery.Client(project=PROJECT_ID)

    target_table = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

    loaded = 0

    for row in rows:
        check_query = """
            SELECT COUNT(*) AS row_count
            FROM `{target_table}`
            WHERE message_id = @message_id
              AND item_sequence = @item_sequence
        """.format(target_table=target_table)

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter(
                    "message_id",
                    "STRING",
                    row["message_id"],
                ),
                bigquery.ScalarQueryParameter(
                    "item_sequence",
                    "INT64",
                    row["item_sequence"],
                ),
            ]
        )

        result = client.query(
            check_query,
            job_config=job_config,
        ).result()

        exists = next(result).row_count > 0

        if exists:
            continue

        errors = client.insert_rows_json(
            target_table,
            [row],
        )

        if errors:
            raise RuntimeError(
                f"Failed to insert BeatStars email sale row: {errors}"
            )

        loaded += 1

    return loaded