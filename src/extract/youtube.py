import pandas as pd
from googleapiclient.discovery import build
from datetime import date


YOUTUBE_ANALYTICS_START_DATE = "2020-03-01"


def get_youtube_service(credentials):
    return build(
        "youtube",
        "v3",
        credentials=credentials,
    )


def get_youtube_analytics_service(credentials):
    return build(
        "youtubeAnalytics",
        "v2",
        credentials=credentials,
    )


def extract_channel_info(credentials):
    youtube = get_youtube_service(credentials)

    response = (
        youtube.channels()
        .list(
            part="snippet,statistics,contentDetails",
            mine=True,
        )
        .execute()
    )

    return response


def extract_all_videos(credentials, uploads_playlist_id):
    youtube = get_youtube_service(credentials)

    videos = []
    next_page_token = None

    while True:
        response = (
            youtube.playlistItems()
            .list(
                part="snippet,contentDetails",
                playlistId=uploads_playlist_id,
                maxResults=50,
                pageToken=next_page_token,
            )
            .execute()
        )

        for video in response.get("items", []):
            videos.append(
                {
                    "video_id": video["contentDetails"]["videoId"],
                    "title": video["snippet"]["title"],
                    "published_at": video["contentDetails"][
                        "videoPublishedAt"
                    ],
                }
            )

        next_page_token = response.get("nextPageToken")

        if not next_page_token:
            break

    return pd.DataFrame(videos)


def extract_video_statistics(credentials, videos_df):
    youtube = get_youtube_service(credentials)

    statistics = []
    video_ids = videos_df["video_id"].tolist()

    for start in range(0, len(video_ids), 50):
        batch = video_ids[start : start + 50]

        response = (
            youtube.videos()
            .list(
                part="statistics,contentDetails",
                id=",".join(batch),
            )
            .execute()
        )

        for video in response.get("items", []):
            stats = video.get("statistics", {})
            content_details = video.get("contentDetails", {})

            statistics.append(
                {
                    "video_id": video["id"],
                    "views": int(stats.get("viewCount", 0)),
                    "likes": int(stats.get("likeCount", 0)),
                    "comments": int(stats.get("commentCount", 0)),
                    "duration": content_details.get("duration"),
                }
            )

    return pd.DataFrame(statistics)


def extract_video_analytics(credentials, videos_df):
    youtube_analytics = get_youtube_analytics_service(credentials)

    start_date = YOUTUBE_ANALYTICS_START_DATE
    end_date = pd.Timestamp.now(tz="UTC").date().isoformat()

    analytics_rows = []
    video_ids = videos_df["video_id"].tolist()

    for start in range(0, len(video_ids), 200):
        batch = video_ids[start : start + 200]

        response = (
            youtube_analytics.reports()
            .query(
                ids="channel==MINE",
                startDate=start_date,
                endDate=end_date,
                dimensions="video",
                filters=f"video=={','.join(batch)}",
                metrics=(
                    "views,"
                    "estimatedMinutesWatched,"
                    "averageViewDuration,"
                    "averageViewPercentage,"
                    "subscribersGained,"
                    "subscribersLost"
                ),
                sort="-views",
                maxResults=200,
            )
            .execute()
        )

        for row in response.get("rows", []):
            analytics_rows.append(
                {
                    "video_id": row[0],
                    "analytics_report_views": int(row[1]),
                    "watch_time_minutes": float(row[2]),
                    "average_view_duration_seconds": float(row[3]),
                    "average_view_percentage": float(row[4]),
                    "subscribers_gained": int(row[5]),
                    "subscribers_lost": int(row[6]),
                }
            )

    return pd.DataFrame(analytics_rows)

def extract_country_views(youtube_analytics):
    response = (
        youtube_analytics.reports()
        .query(
            ids="channel==MINE",
            startDate="2020-03-01",
            endDate=date.today().isoformat(),
            metrics="views",
            dimensions="country",
            sort="-views",
        )
        .execute()
    )

    rows = response.get("rows", [])

    return pd.DataFrame(
        rows,
        columns=[
            "country_code",
            "views",
        ],
    )