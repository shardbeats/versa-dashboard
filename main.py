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
    run_bigquery_query,
)
from src.load.youtube import load_youtube_to_silver

from src.transform.beatstars import (
    clean_beatstars_sales,
    validate_beatstars_sales,
)
from src.transform.gold import (
    BEATSTARS_SALES_PERFORMANCE_QUERY,
    CROSS_PLATFORM_BEAT_PERFORMANCE_QUERY,
    DIM_BEAT_QUERY,
    BEATSTARS_MATCHING_RULES_QUERY,
    YOUTUBE_VIDEO_PERFORMANCE_QUERY,
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

YOUTUBE_COUNTRY_TABLE_ID = (
    f"{PROJECT_ID}.gold.youtube_country_performance"
)


def load_country_performance_to_bigquery(
    country_df,
):
    """
    Replace the YouTube country-performance table in BigQuery Gold.
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


def run_youtube_pipeline():
    """
    Run the complete YouTube pipeline:
    Extract -> Transform -> Validate -> Silver -> BigQuery -> Gold
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

    # Load YouTube metrics to BigQuery Silver.
    load_dataframe_to_bigquery(
        dataframe=fact_youtube_video_metrics,
        table_name="fact_youtube_video_metrics",
        write_disposition=(
            bigquery.WriteDisposition.WRITE_TRUNCATE
        ),
    )

    # Build YouTube Gold.
    run_bigquery_query(
        YOUTUBE_VIDEO_PERFORMANCE_QUERY
    )

    print(
        "\nYouTube pipeline completed successfully."
    )


def run_beatstars_pipeline():
    """
    Run the complete BeatStars pipeline:
    Extract -> Transform -> Validate -> Silver -> BigQuery -> Gold
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

    # Create manual BeatStars overrides.
    run_bigquery_query(
        BEATSTARS_MATCHING_RULES_QUERY
    )

    # Build BeatStars Gold.
    run_bigquery_query(
        BEATSTARS_SALES_PERFORMANCE_QUERY
    )

    # Build the shared Beat dimension.
    run_bigquery_query(
        DIM_BEAT_QUERY
    )

    # Build cross-platform Gold.
    run_bigquery_query(
        CROSS_PLATFORM_BEAT_PERFORMANCE_QUERY
    )

    print(
        "\nBeatStars pipeline completed successfully."
    )


def run_full_pipeline():
    """
    Run both the YouTube and BeatStars pipelines.
    """

    run_youtube_pipeline()
    run_beatstars_pipeline()


def main():
    print(
        "\n========== MAAM PIPELINE STARTED ==========\n"
    )

    run_full_pipeline()

    print(
        "\n========== MAAM PIPELINE COMPLETED ==========\n"
    )


if __name__ == "__main__":
    main()