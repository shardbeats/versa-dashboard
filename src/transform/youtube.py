import pandas as pd


CAREER_START_DATE = pd.Timestamp(
    "2020-03-01",
    tz="UTC",
)


def parse_beat_name(title: str) -> str:
    """
    Extract the beat name from a standard YouTube title.

    Example:
    (FREE) Key Glock Type Beat 2026 - "Trapped" | Type Beat
    becomes:
    Trapped
    """

    title = str(title).strip()

    # Shorts and older videos may not follow our normal title format.
    if " - " not in title:
        return title

    beat_name = title.split(
        " - ",
        maxsplit=1,
    )[1]

    # Remove everything after the first pipe.
    beat_name = beat_name.split(
        "|",
        maxsplit=1,
    )[0].strip()

    # Remove straight and curly quotation marks.
    beat_name = beat_name.strip(
        "\"'“”‘’"
    )

    return beat_name.strip()


def parse_youtube_duration(duration: str) -> int:
    """
    Convert a YouTube ISO 8601 duration into seconds.

    Example:
    PT3M30S becomes 210.
    """

    parsed_duration = pd.to_timedelta(duration)

    return int(
        parsed_duration.total_seconds()
    )


def clean_youtube_metadata(
    videos_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Clean the metadata returned from the uploads playlist.
    """

    videos_df = videos_df.copy()

    videos_df["published_at"] = pd.to_datetime(
        videos_df["published_at"],
        utc=True,
    )

    videos_df = (
        videos_df.drop_duplicates(
            subset=["video_id"],
            keep="first",
        )
        .reset_index(drop=True)
    )

    videos_df["beat_name"] = videos_df["title"].apply(
        parse_beat_name
    )

    return videos_df


def merge_video_statistics(
    videos_df: pd.DataFrame,
    statistics_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge video metadata with public YouTube statistics.

    Videos without returned statistics or duration are excluded,
    because they cannot be represented reliably in our model.
    """

    videos_df = videos_df.copy()
    statistics_df = statistics_df.copy()

    enriched_videos_df = videos_df.merge(
        statistics_df,
        on="video_id",
        how="left",
        validate="one_to_one",
    )

    missing_duration = (
        enriched_videos_df["duration"].isna()
    )

    if missing_duration.any():
        missing_videos = enriched_videos_df.loc[
            missing_duration,
            [
                "video_id",
                "title",
            ],
        ]

        print(
            "\nSkipping "
            f"{len(missing_videos)} video(s) "
            "without available duration/statistics:"
        )

        print(
            missing_videos.to_string(
                index=False
            )
        )

        enriched_videos_df = (
            enriched_videos_df.loc[
                ~missing_duration
            ]
            .copy()
            .reset_index(drop=True)
        )

    integer_columns = [
        "views",
        "likes",
        "comments",
    ]

    enriched_videos_df[integer_columns] = (
        enriched_videos_df[integer_columns]
        .fillna(0)
        .astype("int64")
    )

    enriched_videos_df["duration_seconds"] = (
        enriched_videos_df["duration"].apply(
            parse_youtube_duration
        )
    )

    return enriched_videos_df


def merge_youtube_analytics(
    videos_df: pd.DataFrame,
    analytics_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge public YouTube data with owner-only Analytics metrics.
    """

    videos_df = videos_df.copy()
    analytics_df = analytics_df.copy()

    analytics_metrics = analytics_df[
        [
            "video_id",
            "watch_time_minutes",
            "average_view_duration_seconds",
            "average_view_percentage",
            "subscribers_gained",
            "subscribers_lost",
            "estimated_revenue",
        ]
    ].copy()

    enriched_videos_df = videos_df.merge(
        analytics_metrics,
        on="video_id",
        how="left",
        validate="one_to_one",
    )

    float_columns = [
        "watch_time_minutes",
        "average_view_duration_seconds",
        "average_view_percentage",
        "estimated_revenue",
    ]

    integer_columns = [
        "subscribers_gained",
        "subscribers_lost",
    ]

    enriched_videos_df[float_columns] = (
        enriched_videos_df[float_columns]
        .fillna(0.0)
        .astype("float64")
    )

    enriched_videos_df[integer_columns] = (
        enriched_videos_df[integer_columns]
        .fillna(0)
        .astype("int64")
    )

    return enriched_videos_df


def create_dim_youtube_video(
    videos_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create the YouTube video dimension table.
    """

    dim_youtube_video = videos_df[
        [
            "video_id",
            "title",
            "beat_name",
            "published_at",
            "duration",
            "duration_seconds",
        ]
    ].copy()

    dim_youtube_video["is_short"] = (
        dim_youtube_video["duration_seconds"]
        <= 60
    )

    dim_youtube_video[
        "is_main_niche_period"
    ] = (
        dim_youtube_video["published_at"]
        >= CAREER_START_DATE
    )

    return dim_youtube_video


def create_fact_youtube_video_metrics(
    videos_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create the current YouTube video metrics snapshot.
    """

    fact_youtube_video_metrics = videos_df[
        [
            "video_id",
            "views",
            "likes",
            "comments",
            "watch_time_minutes",
            "average_view_duration_seconds",
            "average_view_percentage",
            "subscribers_gained",
            "subscribers_lost",
            "estimated_revenue",
        ]
    ].copy()

    fact_youtube_video_metrics[
        "snapshot_timestamp"
    ] = pd.Timestamp.now(
        tz="UTC"
    )

    return fact_youtube_video_metrics


def validate_youtube_data(
    videos_df: pd.DataFrame,
) -> None:
    """
    Print a basic data-quality report for YouTube Silver.
    """

    print(
        "\n--- YouTube data quality report ---"
    )

    print(f"Rows: {len(videos_df)}")
    print(
        f"Columns: {len(videos_df.columns)}"
    )
    print(
        "Unique video IDs: "
        f"{videos_df['video_id'].nunique()}"
    )

    duplicate_video_ids = videos_df.duplicated(
        subset=["video_id"],
        keep=False,
    )

    print(
        "Rows with duplicated video IDs: "
        f"{duplicate_video_ids.sum()}"
    )

    print("\nMissing values:")
    print(videos_df.isna().sum())

    print("\nData types:")
    print(videos_df.dtypes)

    print("--- End of report ---\n")