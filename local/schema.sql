-- MAAM local SQLite schema (sin BigQuery / sin dbt)
-- Guarda historico diario para multi-canal

PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS channels (
  channel_id TEXT PRIMARY KEY,
  title TEXT,
  description TEXT DEFAULT '',
  thumbnail_url TEXT DEFAULT '',
  uploads_playlist_id TEXT,
  fetched_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS channel_snapshots (
  channel_id TEXT NOT NULL,
  snapshot_date TEXT NOT NULL,
  subs INTEGER DEFAULT 0,
  views INTEGER DEFAULT 0,
  video_count INTEGER DEFAULT 0,
  PRIMARY KEY (channel_id, snapshot_date),
  FOREIGN KEY (channel_id) REFERENCES channels(channel_id)
);

CREATE TABLE IF NOT EXISTS videos (
  video_id TEXT PRIMARY KEY,
  channel_id TEXT,
  title TEXT,
  beat_name TEXT,
  beat_key TEXT,
  published_at TEXT,
  duration TEXT,
  duration_seconds INTEGER,
  is_short INTEGER DEFAULT 0,
  tags TEXT DEFAULT '',
  tags_count INTEGER DEFAULT 0,
  description_len INTEGER DEFAULT 0,
  category_id TEXT DEFAULT '',
  views_per_day REAL DEFAULT 0,
  engagement_rate REAL DEFAULT 0,
  seo_score INTEGER DEFAULT 0,
  FOREIGN KEY (channel_id) REFERENCES channels(channel_id)
);

CREATE TABLE IF NOT EXISTS video_metrics_snapshots (
  video_id TEXT NOT NULL,
  snapshot_date TEXT NOT NULL,
  views INTEGER DEFAULT 0,
  likes INTEGER DEFAULT 0,
  comments INTEGER DEFAULT 0,
  watch_time_minutes REAL DEFAULT 0,
  avg_view_duration_seconds REAL DEFAULT 0,
  avg_view_percentage REAL DEFAULT 0,
  subs_gained INTEGER DEFAULT 0,
  subs_lost INTEGER DEFAULT 0,
  estimated_revenue REAL DEFAULT 0,
  snapshot_timestamp TEXT NOT NULL,
  PRIMARY KEY (video_id, snapshot_date),
  FOREIGN KEY (video_id) REFERENCES videos(video_id)
);

CREATE TABLE IF NOT EXISTS beatstars_sales (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  product_name TEXT,
  beat_key TEXT,
  product_type TEXT,
  quantity REAL DEFAULT 1,
  gross_amount REAL DEFAULT 0,
  discounts REAL DEFAULT 0,
  collab_amount REAL DEFAULT 0,
  beatstars_fee REAL DEFAULT 0,
  net_revenue REAL DEFAULT 0,
  imported_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS country_views (
  snapshot_date TEXT NOT NULL,
  country_code TEXT NOT NULL,
  views INTEGER DEFAULT 0,
  PRIMARY KEY (snapshot_date, country_code)
);

-- Analytics profundo (ultimos 28d, un snapshot por dia)
CREATE TABLE IF NOT EXISTS traffic_sources (
  snapshot_date TEXT NOT NULL,
  source TEXT NOT NULL,
  views INTEGER DEFAULT 0,
  watch_minutes REAL DEFAULT 0,
  PRIMARY KEY (snapshot_date, source)
);

CREATE TABLE IF NOT EXISTS device_views (
  snapshot_date TEXT NOT NULL,
  device TEXT NOT NULL,
  views INTEGER DEFAULT 0,
  watch_minutes REAL DEFAULT 0,
  PRIMARY KEY (snapshot_date, device)
);

CREATE TABLE IF NOT EXISTS search_terms (
  snapshot_date TEXT NOT NULL,
  term TEXT NOT NULL,
  views INTEGER DEFAULT 0,
  PRIMARY KEY (snapshot_date, term)
);

CREATE TABLE IF NOT EXISTS demographics (
  snapshot_date TEXT NOT NULL,
  age_group TEXT NOT NULL,
  gender TEXT NOT NULL,
  views INTEGER DEFAULT 0,
  watch_minutes REAL DEFAULT 0,
  PRIMARY KEY (snapshot_date, age_group, gender)
);

CREATE TABLE IF NOT EXISTS video_impressions (
  video_id TEXT NOT NULL,
  snapshot_date TEXT NOT NULL,
  views_28d INTEGER DEFAULT 0,
  impressions_28d INTEGER DEFAULT 0,
  ctr_28d REAL DEFAULT 0,
  PRIMARY KEY (video_id, snapshot_date)
);

-- Vistas tipo Gold (reemplazo minimo de dbt)
CREATE VIEW IF NOT EXISTS v_video_latest AS
SELECT v.*, m.*
FROM videos v
LEFT JOIN video_metrics_snapshots m ON m.video_id = v.video_id
WHERE (m.snapshot_date IS NULL OR m.snapshot_date = (
  SELECT MAX(snapshot_date) FROM video_metrics_snapshots WHERE video_id = v.video_id
));

CREATE VIEW IF NOT EXISTS v_channel_growth AS
SELECT channel_id, snapshot_date, subs, views, video_count,
  subs - LAG(subs) OVER (PARTITION BY channel_id ORDER BY snapshot_date) AS subs_delta,
  views - LAG(views) OVER (PARTITION BY channel_id ORDER BY snapshot_date) AS views_delta
FROM channel_snapshots
ORDER BY channel_id, snapshot_date;

-- Velocidad real: diferencia entre los 2 ultimos snapshots por video
CREATE VIEW IF NOT EXISTS v_video_velocity AS
WITH r AS (
  SELECT video_id, snapshot_date, views,
    LAG(views) OVER (PARTITION BY video_id ORDER BY snapshot_date) AS prev_views,
    LAG(snapshot_date) OVER (PARTITION BY video_id ORDER BY snapshot_date) AS prev_date
  FROM video_metrics_snapshots
)
SELECT video_id, snapshot_date, views,
  COALESCE(views - prev_views, 0) AS views_gain,
  COALESCE(julianday(snapshot_date) - julianday(prev_date), 0) AS days_diff,
  CASE WHEN COALESCE(julianday(snapshot_date) - julianday(prev_date), 0) > 0
       THEN (views - prev_views) / (julianday(snapshot_date) - julianday(prev_date))
       ELSE 0 END AS views_per_day_real
FROM r
WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM video_metrics_snapshots);

CREATE VIEW IF NOT EXISTS v_beat_cross AS
-- Cruce por beat_key (minusculas, sin acentos ni puntuacion)
SELECT
  COALESCE(v.beat_name, b.product_name) AS beat,
  SUM(b.net_revenue) AS beatstars_revenue,
  COUNT(b.id) AS beat_sales,
  SUM(m.views) AS yt_views,
  SUM(m.estimated_revenue) AS yt_revenue
FROM videos v
LEFT JOIN video_metrics_snapshots m
  ON m.video_id = v.video_id
  AND m.snapshot_date = (SELECT MAX(snapshot_date) FROM video_metrics_snapshots WHERE video_id = v.video_id)
LEFT JOIN beatstars_sales b
  ON b.beat_key = v.beat_key AND b.beat_key <> ''
GROUP BY 1;
