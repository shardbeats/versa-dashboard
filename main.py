import argparse
import subprocess
from pathlib import Path

from src.extract.beatstars_email import (
    extract_beatstars_sales as extract_beatstars_email_sales,
)
from src.load.beatstars_email import load_beatstars_email_sales


from google.cloud import bigquery
from googleapiclient.discovery import build

from src.auth import authenticate

from src.extract.beatstars import extract_beatstars_sales
from src.extract.youtube import (
    extract_all_videos,
    extract_channel_info,
    extract_country_views,
    extract_video_analytics,
    extract_video_statistics,
)

from src.load.beatstars import load_beatstars_sales_to_silver
from src.load.bigquery import (
    load_dataframe_to_bigquery,
    load_daily_snapshot_to_bigquery,
)
from src.load.youtube import load_youtube_to_silver

from src.transform.beatstars import (
    clean_beatstars_sales,
    validate_beatstars_sales,
)
from src.transform.youtube import (
    clean_youtube_metadata,
    create_dim_youtube_video,
    create_fact_youtube_video_metrics,
    merge_video_statistics,
    merge_youtube_analytics,
    validate_youtube_data,
)


PROJECT_ID = "versa-dashboard"

DBT_PROJECT_DIR = (
    Path(__file__).resolve().parent
    / "dbt"
    / "maam"
)

YOUTUBE_COUNTRY_TABLE_ID = (
    f"{PROJECT_ID}.gold.youtube_country_performance"
)


def load_country_performance_to_bigquery(
    country_df,
):
    """
    Replace the YouTube country-performance table in BigQuery Gold.

    This table is loaded directly because it currently comes from a
    standalone API response rather than a BigQuery Silver source.
    """

    client = bigquery.Client(
        project=PROJECT_ID
    )

    job_config = bigquery.LoadJobConfig(
        write_disposition=(
            bigquery.WriteDisposition.WRITE_TRUNCATE
        ),
    )

    load_job = client.load_table_from_dataframe(
        country_df,
        YOUTUBE_COUNTRY_TABLE_ID,
        job_config=job_config,
    )

    load_job.result()

    print(
        f"\nLoaded {len(country_df)} rows to "
        f"{YOUTUBE_COUNTRY_TABLE_ID}"
    )


def run_dbt_build():
    """
    Build and test the complete dbt Gold layer.
    """

    print(
        "\n========== MAAM DBT BUILD STARTED ==========\n"
    )

    if not DBT_PROJECT_DIR.exists():
        raise FileNotFoundError(
            "dbt project directory was not found: "
            f"{DBT_PROJECT_DIR}"
        )

    try:
        subprocess.run(
            [
        "dbt",
        "build",
        "--project-dir",
        "dbt/maam",
        "--profiles-dir",
        "dbt/maam",
            ],
    check=True,
        )

    except FileNotFoundError as error:
        raise RuntimeError(
            "The dbt executable could not be found. "
            "Make sure the virtual environment is active "
            "and dbt-bigquery is installed."
        ) from error

    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            "dbt build failed. Check the dbt output above "
            "for the failing model or test."
        ) from error

    print(
        "\n========== MAAM DBT BUILD COMPLETED ==========\n"
    )

def run_dbt_model(model_name):
    """
    Build a specific dbt model.
    """

    print(
        f"\n========== MAAM DBT MODEL STARTED: "
        f"{model_name} ==========\n"
    )

    if not DBT_PROJECT_DIR.exists():
        raise FileNotFoundError(
            "dbt project directory was not found: "
            f"{DBT_PROJECT_DIR}"
        )

    try:
        subprocess.run(
            [
                "dbt",
                "run",
                "--select",
                model_name,
                "--project-dir",
                "dbt/maam",
                "--profiles-dir",
                "dbt/maam",
            ],
            check=True,
        )

    except FileNotFoundError as error:
        raise RuntimeError(
            "The dbt executable could not be found. "
            "Make sure the virtual environment is active "
            "and dbt-bigquery is installed."
        ) from error

    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            f"dbt run failed for model '{model_name}'. "
            "Check the dbt output above."
        ) from error

    print(
        f"\n========== MAAM DBT MODEL COMPLETED: "
        f"{model_name} ==========\n"
    )

def run_youtube_pipeline():
    """
    Run the YouTube pipeline:
    Extract -> Transform -> Validate -> Silver -> BigQuery Silver
    """

    credentials = authenticate()

    # Create the YouTube Analytics API service.
    youtube_analytics = build(
        "youtubeAnalytics",
        "v2",
        credentials=credentials,
    )

    # Extract country-level YouTube views.
    country_df = extract_country_views(
        youtube_analytics
    )

    # Load country-level data directly to BigQuery Gold.
    load_country_performance_to_bigquery(
        country_df
    )

    # Extract channel information.
    channel = extract_channel_info(
        credentials
    )

    channel_item = channel["items"][0]

    uploads_playlist_id = (
        channel_item["contentDetails"]
        ["relatedPlaylists"]
        ["uploads"]
    )

    # Extract video metadata.
    videos_df = extract_all_videos(
        credentials,
        uploads_playlist_id,
    )

    # Clean metadata before later API requests.
    videos_df = clean_youtube_metadata(
        videos_df
    )

    # Extract public video statistics.
    statistics_df = extract_video_statistics(
        credentials,
        videos_df,
    )

    # Merge metadata with public statistics.
    videos_df = merge_video_statistics(
        videos_df,
        statistics_df,
    )

    # Extract owner-only YouTube Analytics metrics.
    analytics_df = extract_video_analytics(
        credentials,
        videos_df,
    )

    # Merge public and owner-only YouTube data.
    videos_df = merge_youtube_analytics(
        videos_df,
        analytics_df,
    )

    # Validate the complete YouTube Silver dataset.
    validate_youtube_data(
        videos_df
    )

    # Create Silver warehouse-style tables.
    dim_youtube_video = create_dim_youtube_video(
        videos_df
    )

    fact_youtube_video_metrics = (
        create_fact_youtube_video_metrics(
            videos_df
        )
    )

    # Save YouTube Silver locally as Parquet.
    load_youtube_to_silver(
        dim_youtube_video,
        fact_youtube_video_metrics,
    )

    # Load YouTube dimension to BigQuery Silver.
    load_dataframe_to_bigquery(
        dataframe=dim_youtube_video,
        table_name="dim_youtube_video",
        write_disposition=(
            bigquery.WriteDisposition.WRITE_TRUNCATE
        ),
    )

    # Load YouTube metrics as a daily historical snapshot.
    load_daily_snapshot_to_bigquery(
        dataframe=fact_youtube_video_metrics,
        table_name="fact_youtube_video_metrics",
    )

    print(
        "\nYouTube Silver pipeline completed successfully."
    )


def run_beatstars_pipeline():
    """
    Run the BeatStars pipeline:
    Extract -> Transform -> Validate -> Silver -> BigQuery Silver
    """

    # Extract raw BeatStars CSV data.
    beatstars_sales_df = extract_beatstars_sales()

    # Transform raw BeatStars data into Silver.
    beatstars_sales_df = clean_beatstars_sales(
        beatstars_sales_df
    )

    # Validate BeatStars Silver data.
    validate_beatstars_sales(
        beatstars_sales_df
    )

    # Save BeatStars Silver locally as Parquet.
    load_beatstars_sales_to_silver(
        beatstars_sales_df
    )

    # Load BeatStars Silver to BigQuery.
    load_dataframe_to_bigquery(
        dataframe=beatstars_sales_df,
        table_name="sales_summary",
        write_disposition=(
            bigquery.WriteDisposition.WRITE_TRUNCATE
        ),
    )

    print(
        "\nBeatStars Silver pipeline completed successfully."
    )

def run_beatstars_email_pipeline():
    """
    Run the fresh BeatStars sales pipeline:

    Gmail -> Parse -> BigQuery staging -> Home dbt model
    """

    sales = extract_beatstars_email_sales(
         max_results=50,
    )

    print(
        f"Found {len(sales)} recent BeatStars sale emails."
    )

    loaded_rows = load_beatstars_email_sales(
        sales
    )

    print(
        f"Loaded {loaded_rows} new BeatStars sale item rows."
    )

    # Refresh the Home metrics using the unified sales view.
    run_dbt_model(
        "homepage_time_intelligence"
    )

def run_full_pipeline():
    """
    Run both source pipelines before dbt builds Gold.
    """

    run_youtube_pipeline()
    run_beatstars_pipeline()


def parse_arguments():
    """
    Parse the pipeline selected from the command line.
    """

    parser = argparse.ArgumentParser(
        description="Run a MAAM data pipeline."
    )

    parser.add_argument(
        "pipeline",
        nargs="?",
        default="full",
        choices=[
            "youtube",
            "beatstars",
            "beatstars_email",
            "full",
        ],
        help=(
            "Pipeline to run: "
            "youtube, beatstars, beatstars_email or full. "
            "Defaults to full."
        ),
    )

    return parser.parse_args()


def main():
    args = parse_arguments()

    print(
        f"\n========== MAAM {args.pipeline.upper()} "
        "PIPELINE STARTED ==========\n"
    )

    if args.pipeline == "youtube":
        run_youtube_pipeline()

    elif args.pipeline == "beatstars":
        run_beatstars_pipeline()

    elif args.pipeline == "beatstars_email":
        run_beatstars_email_pipeline()

    else:
        run_full_pipeline()

    # Build the complete Gold layer for the regular pipelines.
    # The BeatStars email pipeline refreshes only the Home model itself.
    if args.pipeline != "beatstars_email":
          run_dbt_build()

    print(
        f"\n========== MAAM {args.pipeline.upper()} "
        "PIPELINE COMPLETED ==========\n"
    )


if __name__ == "__main__":
    main()