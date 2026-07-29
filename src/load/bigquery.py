import pandas as pd
from google.cloud import bigquery


PROJECT_ID = "versa-dashboard"
DATASET_ID = "silver"
LOCATION = "EU"


def get_bigquery_client():
    """
    Create an authenticated BigQuery client.
    """

    return bigquery.Client(
        project=PROJECT_ID,
        location=LOCATION,
    )


def load_dataframe_to_bigquery(
    dataframe: pd.DataFrame,
    table_name: str,
    write_disposition: str,
) -> None:
    """
    Load a pandas DataFrame into a BigQuery table.

    Args:
        dataframe:
            The DataFrame to load.

        table_name:
            Destination table name inside the Silver dataset.

        write_disposition:
            Controls what happens if the table already exists.
            Examples:
            - bigquery.WriteDisposition.WRITE_TRUNCATE
            - bigquery.WriteDisposition.WRITE_APPEND
    """

    client = get_bigquery_client()

    table_id = (
        f"{PROJECT_ID}."
        f"{DATASET_ID}."
        f"{table_name}"
    )

    job_config = bigquery.LoadJobConfig(
        write_disposition=write_disposition,
    )

    load_job = client.load_table_from_dataframe(
        dataframe,
        table_id,
        job_config=job_config,
        location=LOCATION,
    )

    # Vänta tills BigQuery har slutfört jobbet.
    load_job.result()

    destination_table = client.get_table(table_id)

    print(
        f"\nLoaded {destination_table.num_rows} rows "
        f"to {table_id}"
    )

def run_bigquery_query(query: str) -> None:
    """
    Run a SQL query in BigQuery and wait for it to finish.
    """

    client = get_bigquery_client()

    query_job = client.query(
        query,
        location=LOCATION,
    )

    query_job.result()

    print("\nBigQuery query completed successfully.")