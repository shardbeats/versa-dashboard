"""Reportes extra de YouTube Analytics (nivel canal + impresiones por video).

Todo es channel==MINE, ultimos 28 dias, para no gastar cuota de mas.
Si un reporte falla (p.ej. sin permisos o sin datos), devuelve DataFrame vacio.
"""
from datetime import date, timedelta

import pandas as pd


def _last28():
    end = date.today().isoformat()
    start = (date.today() - timedelta(days=28)).isoformat()
    return start, end


def _safe_query(yt_analytics, **kwargs) -> dict:
    try:
        return yt_analytics.reports().query(**kwargs).execute()
    except Exception as e:
        print(f"[warn] analytics skip {kwargs.get('dimensions')}: {e}")
        return {}


def extract_traffic_sources(yt_analytics) -> pd.DataFrame:
    start, end = _last28()
    resp = _safe_query(
        yt_analytics, ids="channel==MINE", startDate=start, endDate=end,
        dimensions="insightTrafficSourceType",
        metrics="views,estimatedMinutesWatched",
        sort="-views", maxResults=25,
    )
    rows = resp.get("rows", []) or []
    return pd.DataFrame(rows, columns=["source", "views", "watch_minutes"])


def extract_devices(yt_analytics) -> pd.DataFrame:
    start, end = _last28()
    resp = _safe_query(
        yt_analytics, ids="channel==MINE", startDate=start, endDate=end,
        dimensions="deviceType",
        metrics="views,estimatedMinutesWatched",
        sort="-views", maxResults=25,
    )
    rows = resp.get("rows", []) or []
    return pd.DataFrame(rows, columns=["device", "views", "watch_minutes"])


def extract_search_terms(yt_analytics) -> pd.DataFrame:
    start, end = _last28()
    resp = _safe_query(
        yt_analytics, ids="channel==MINE", startDate=start, endDate=end,
        dimensions="insightTrafficSourceDetail",
        filters="insightTrafficSourceType==YT_SEARCH",
        metrics="views",
        sort="-views", maxResults=25,
    )
    rows = resp.get("rows", []) or []
    return pd.DataFrame(rows, columns=["term", "views"])


def extract_demographics(yt_analytics) -> pd.DataFrame:
    # La API solo acepta viewerPercentage con ageGroup,gender (no views).
    start, end = _last28()
    resp = _safe_query(
        yt_analytics, ids="channel==MINE", startDate=start, endDate=end,
        dimensions="ageGroup,gender",
        metrics="viewerPercentage",
        sort="ageGroup,gender",
    )
    rows = resp.get("rows", []) or []
    df = pd.DataFrame(rows, columns=["age_group", "gender", "views"])
    if not df.empty:
        df["watch_minutes"] = 0.0
    else:
        df = pd.DataFrame(columns=["age_group", "gender", "views", "watch_minutes"])
    return df


def extract_video_views_28d(credentials, videos_df) -> pd.DataFrame:
    """Views 28d por video (para velocidad/outliers reales). 1 query por lote de 200."""
    from googleapiclient.discovery import build

    yt_analytics = build("youtubeAnalytics", "v2", credentials=credentials)
    start, end = _last28()
    ids = videos_df["video_id"].tolist() if videos_df is not None else []
    rows = []
    for i in range(0, len(ids), 200):
        batch = ids[i:i + 200]
        resp = _safe_query(
            yt_analytics, ids="channel==MINE", startDate=start, endDate=end,
            dimensions="video",
            filters=f"video=={','.join(batch)}",
            metrics="views,estimatedMinutesWatched",
            sort="-views", maxResults=200,
        )
        for r in resp.get("rows", []) or []:
            rows.append({
                "video_id": r[0],
                "views_28d": int(r[1]),
                "impressions_28d": 0,
                "ctr_28d": 0.0,
            })
    return pd.DataFrame(rows)


def extract_video_impressions(credentials, videos_df) -> pd.DataFrame:
    """Compat: ahora devuelve views_28d (CTR/impresiones viven en Reporting API bulk, no en query)."""
    return extract_video_views_28d(credentials, videos_df)
