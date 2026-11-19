"""Pipeline YouTube local -> SQLite (reusa extract/transform original)."""
from datetime import datetime, timezone
import pandas as pd

from src.auth import authenticate
from src.extract.youtube import (
    extract_all_videos,
    extract_channel_info,
    extract_country_views,
    extract_video_analytics,
    extract_video_statistics,
)
from src.transform.youtube import (
    clean_youtube_metadata,
    create_dim_youtube_video,
    create_fact_youtube_video_metrics,
    merge_video_statistics,
    merge_youtube_analytics,
    validate_youtube_data,
)

from .db import get_conn
from .matching import beat_key, extract_beat_name


def today_str() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def run_youtube_local(db_path=None, max_videos: int | None = None):
    creds = authenticate()

    # 1. Canal (mine=True, como original)
    channel = extract_channel_info(creds)
    item = channel["items"][0]
    channel_id = item["id"]
    title = item["snippet"]["title"]
    stats = item.get("statistics", {})
    uploads_playlist_id = item["contentDetails"]["relatedPlaylists"]["uploads"]

    # 2. Videos
    videos_df = extract_all_videos(creds, uploads_playlist_id)
    if max_videos:
        videos_df = videos_df.head(max_videos)
    videos_df = clean_youtube_metadata(videos_df)
    # Parser mejorado: tambien entiende '"Beat" | resto' (sin ' - ')
    videos_df["beat_name"] = videos_df["title"].apply(extract_beat_name)

    statistics_df = extract_video_statistics(creds, videos_df)
    videos_df = merge_video_statistics(videos_df, statistics_df)

    try:
        analytics_df = extract_video_analytics(creds, videos_df)
        videos_df = merge_youtube_analytics(videos_df, analytics_df)
    except Exception as e:
        print(f"\n[warn] Analytics API no disponible, sigo solo con Data API: {e}")
        # create_fact exige estas columnas: las relleno con 0 para modo solo-Data-API
        for col, default in [
            ("watch_time_minutes", 0.0),
            ("average_view_duration_seconds", 0.0),
            ("average_view_percentage", 0.0),
            ("estimated_revenue", 0.0),
            ("subscribers_gained", 0),
            ("subscribers_lost", 0),
        ]:
            if col not in videos_df.columns:
                videos_df[col] = default

    validate_youtube_data(videos_df)

    dim = create_dim_youtube_video(videos_df)
    fact = create_fact_youtube_video_metrics(videos_df)

    snapshot_date = today_str()
    now_iso = datetime.now(timezone.utc).isoformat()

    conn = get_conn(db_path)
    cur = conn.cursor()

    cur.execute(
        "INSERT OR REPLACE INTO channels(channel_id, title, uploads_playlist_id, fetched_at) VALUES (?,?,?,?)",
        (channel_id, title, uploads_playlist_id, now_iso),
    )
    cur.execute(
        "INSERT OR REPLACE INTO channel_snapshots(channel_id, snapshot_date, subs, views, video_count) VALUES (?,?,?,?,?)",
        (
            channel_id,
            snapshot_date,
            int(stats.get("subscriberCount", 0) or 0),
            int(stats.get("viewCount", 0) or 0),
            int(stats.get("videoCount", 0) or 0),
        ),
    )

    for _, r in dim.iterrows():
        bk = beat_key(r.get("beat_name", ""))
        cur.execute(
            """INSERT OR REPLACE INTO videos
               (video_id, channel_id, title, beat_name, beat_key, published_at, duration, duration_seconds, is_short)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                r["video_id"],
                channel_id,
                str(r["title"]),
                str(r.get("beat_name", "")),
                bk,
                str(r["published_at"]),
                str(r["duration"]),
                int(r["duration_seconds"]),
                1 if bool(r.get("is_short")) else 0,
            ),
        )

    for _, r in fact.iterrows():
        cur.execute(
            """INSERT OR REPLACE INTO video_metrics_snapshots
               (video_id, snapshot_date, views, likes, comments, watch_time_minutes,
                avg_view_duration_seconds, avg_view_percentage, subs_gained, subs_lost,
                estimated_revenue, snapshot_timestamp)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                r["video_id"],
                snapshot_date,
                int(r.get("views", 0)),
                int(r.get("likes", 0)),
                int(r.get("comments", 0)),
                float(r.get("watch_time_minutes", 0)),
                float(r.get("average_view_duration_seconds", 0)),
                float(r.get("average_view_percentage", 0)),
                int(r.get("subscribers_gained", 0)),
                int(r.get("subscribers_lost", 0)),
                float(r.get("estimated_revenue", 0)),
                str(r.get("snapshot_timestamp", now_iso)),
            ),
        )

    # Country views (best effort, no rompe si falla)
    try:
        from googleapiclient.discovery import build

        yt_analytics = build("youtubeAnalytics", "v2", credentials=creds)
        country_df = extract_country_views(yt_analytics)
        for _, r in country_df.iterrows():
            cur.execute(
                "INSERT OR REPLACE INTO country_views(snapshot_date, country_code, views) VALUES (?,?,?)",
                (snapshot_date, r["country_code"], int(r["views"])),
            )
    except Exception as e:
        print(f"[warn] country views skip: {e}")

    conn.commit()

    n_videos = cur.execute("SELECT COUNT(*) FROM videos").fetchone()[0]
    n_snaps = cur.execute(
        "SELECT COUNT(*) FROM video_metrics_snapshots WHERE snapshot_date=?",
        (snapshot_date,),
    ).fetchone()[0]
    conn.close()

    print(f"\nOK YouTube -> SQLite ({snapshot_date}) canal {title} [{channel_id}]")
    print(f"videos totales: {n_videos}, snapshots hoy: {n_snaps}")
    return {"channel_id": channel_id, "snapshot_date": snapshot_date}
