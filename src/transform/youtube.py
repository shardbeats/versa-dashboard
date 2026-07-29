import pandas as pd


CAREER_START_DATE = pd.Timestamp(
    "2020-03-01",
    tz="UTC",
)


def parse_youtube_duration(duration):
    duration = pd.to_timedelta(duration)

    return int(duration.total_seconds())


def clean_youtube_metadata(videos_df):
    videos_df = videos_df.copy()

    videos_df["published_at"] = pd.to_datetime(
        videos_df["published_at"],
        utc=True,
    )

    videos_df = videos_df.drop_duplicates(
        subset=["video_id"],
        keep="first",
    ).reset_index(drop=True)

    videos_df = add_beat_name(videos_df)

    return videos_df


def merge_video_statistics(videos_df, statistics_df):
    videos_df = videos_df.copy()
    statistics_df = statistics_df.copy()

    enriched_videos_df = videos_df.merge(
        statistics_df,
        on="video_id",
        how="left",
        validate="one_to_one",
    )

    numeric_columns = [
        "views",
        "likes",
        "comments",
    ]

    enriched_videos_df[numeric_columns] = (
        enriched_videos_df[numeric_columns]
        .fillna(0)
        .astype("int64")
    )

    if "duration" in enriched_videos_df.columns:
        enriched_videos_df["duration_seconds"] = (
            enriched_videos_df["duration"].apply(
                parse_youtube_duration
            )
        )

    return enriched_videos_df


def merge_youtube_analytics(videos_df, analytics_df):
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
    ]

    integer_columns = [
        "subscribers_gained",
        "subscribers_lost",
    ]

    enriched_videos_df[float_columns] = enriched_videos_df[
        float_columns
    ].fillna(0.0)

    enriched_videos_df[integer_columns] = (
        enriched_videos_df[integer_columns]
        .fillna(0)
        .astype("int64")
    )

    return enriched_videos_df


def create_dim_youtube_video(videos_df):
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
        dim_youtube_video["duration_seconds"] <= 60
    )

    dim_youtube_video["is_main_niche_period"] = (
        dim_youtube_video["published_at"] >= CAREER_START_DATE
    )

    return dim_youtube_video


def create_fact_youtube_video_metrics(videos_df):
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
        ]
    ].copy()

    fact_youtube_video_metrics["snapshot_timestamp"] = (
        pd.Timestamp.now(tz="UTC")
    )

    return fact_youtube_video_metrics


def parse_beat_name(title):
    beat_name = title

    if " - " in beat_name:
        beat_name = beat_name.rsplit(" - ", 1)[1]

    if " | " in beat_name:
        beat_name = beat_name.split(" | ", 1)[0]

    beat_name = beat_name.strip()

    if (
        len(beat_name) >= 2
        and beat_name[0] in {'"', "'"}
        and beat_name[-1] == beat_name[0]
    ):
        beat_name = beat_name[1:-1].strip()

    return beat_name


def add_beat_name(videos_df):
    videos_df = videos_df.copy()

    videos_df["beat_name"] = videos_df["title"].apply(
        parse_beat_name
    )

    return videos_df

def validate_youtube_data(videos_df):
    print("\n--- YouTube data quality report ---")

    print(f"Rows: {len(videos_df)}")
    print(f"Columns: {len(videos_df.columns)}")
    print(f"Unique video IDs: {videos_df['video_id'].nunique()}")

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