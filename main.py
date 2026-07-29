from src.auth import authenticate
from src.extract.youtube import (
    extract_all_videos,
    extract_channel_info,
    extract_video_analytics,
    extract_video_statistics,
)
from src.load.youtube import load_youtube_to_silver
from src.transform.youtube import (
    clean_youtube_metadata,
    create_dim_youtube_video,
    create_fact_youtube_video_metrics,
    merge_video_statistics,
    merge_youtube_analytics,
    validate_youtube_data,
)


def main():
    credentials = authenticate()

    # Extract channel information
    channel = extract_channel_info(credentials)
    channel_item = channel["items"][0]

    uploads_playlist_id = (
        channel_item["contentDetails"]["relatedPlaylists"]["uploads"]
    )

    # Extract video metadata
    videos_df = extract_all_videos(
        credentials,
        uploads_playlist_id,
    )

    # Clean metadata before using video IDs in later requests
    videos_df = clean_youtube_metadata(videos_df)

    # Extract and merge public video statistics
    statistics_df = extract_video_statistics(
        credentials,
        videos_df,
    )

    videos_df = merge_video_statistics(
        videos_df,
        statistics_df,
    )

    # Extract and merge owner-only Analytics metrics
    analytics_df = extract_video_analytics(
        credentials,
        videos_df,
    )

    videos_df = merge_youtube_analytics(
        videos_df,
        analytics_df,
    )

    # Validate the complete Silver dataset
    validate_youtube_data(videos_df)

    # Create Silver warehouse-style tables
    dim_youtube_video = create_dim_youtube_video(videos_df)

    fact_youtube_video_metrics = (
        create_fact_youtube_video_metrics(videos_df)
    )

    # Load tables to Silver Parquet files
    load_youtube_to_silver(
        dim_youtube_video,
        fact_youtube_video_metrics,
    )

    print("\nDIM_YOUTUBE_VIDEO")
    print(dim_youtube_video)
    print(dim_youtube_video.shape)

    print("\nFACT_YOUTUBE_VIDEO_METRICS")
    print(fact_youtube_video_metrics)
    print(fact_youtube_video_metrics.shape)


if __name__ == "__main__":
    main()