"""Datos extra por video (snippet: tags, descripcion) + metricas estilo vidIQ."""
import pandas as pd
from googleapiclient.discovery import build


def extract_video_snippets(credentials, videos_df) -> pd.DataFrame:
    """Trae tags, descripcion y categoria (1 unidad de cuota por llamada, igual que statistics)."""
    youtube = build("youtube", "v3", credentials=credentials)
    rows = []
    ids = videos_df["video_id"].tolist()
    for start in range(0, len(ids), 50):
        batch = ids[start:start + 50]
        resp = youtube.videos().list(part="snippet", id=",".join(batch)).execute()
        for v in resp.get("items", []):
            sn = v.get("snippet", {})
            tags = sn.get("tags", []) or []
            desc = sn.get("description", "") or ""
            rows.append({
                "video_id": v["id"],
                "tags": ",".join(tags),
                "tags_count": len(tags),
                "description_len": len(desc),
                "category_id": sn.get("categoryId", ""),
            })
    return pd.DataFrame(rows)


def compute_video_metrics(videos_df: pd.DataFrame) -> pd.DataFrame:
    """Agrega views/dia, engagement y SEO score (0-100) estilo vidIQ."""
    df = videos_df.copy()
    now = pd.Timestamp.now(tz="UTC")
    days = ((now - pd.to_datetime(df["published_at"], utc=True)).dt.total_seconds() / 86400).clip(lower=1)
    df["views_per_day"] = (df["views"] / days).round(1)
    df["engagement_rate"] = ((df["likes"] + df["comments"]) / df["views"].replace(0, pd.NA) * 100).fillna(0).round(2)

    title_len = df["title"].str.len()
    desc = pd.to_numeric(df.get("description_len", 0), errors="coerce").fillna(0)
    tags = pd.to_numeric(df.get("tags_count", 0), errors="coerce").fillna(0)
    med_eng = df["engagement_rate"].median()
    med_vpd = df["views_per_day"].median()

    score = (
        ((title_len >= 30) & (title_len <= 70)).astype(int) * 25 +
        (desc >= 200).astype(int) * 25 +
        ((tags >= 5) & (tags <= 15)).astype(int) * 25 +
        ((df["engagement_rate"] >= med_eng) | (df["views_per_day"] >= med_vpd)).astype(int) * 25
    )
    df["seo_score"] = score.astype(int)
    return df


def checklist_for_video(row: pd.Series, med_eng: float, med_vpd: float) -> list[tuple[str, bool, str]]:
    tl = len(str(row.get("title", "")))
    desc = int(row.get("description_len", 0) or 0)
    tags = int(row.get("tags_count", 0) or 0)
    return [
        ("Titulo 30-70 caracteres", 30 <= tl <= 70, f"{tl} caracteres"),
        ("Descripcion +200 caracteres", desc >= 200, f"{desc} caracteres"),
        ("Entre 5 y 15 tags", 5 <= tags <= 15, f"{tags} tags"),
        ("Engagement sobre la mediana", float(row.get("engagement_rate", 0) or 0) >= med_eng,
         f"{row.get('engagement_rate', 0)}% vs mediana {med_eng:.2f}%"),
        ("Views/dia sobre la mediana", float(row.get("views_per_day", 0) or 0) >= med_vpd,
         f"{row.get('views_per_day', 0)} vs mediana {med_vpd:.1f}"),
    ]
