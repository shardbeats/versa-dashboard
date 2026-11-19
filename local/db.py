"""SQLite helper for MAAM local."""
from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().parent / "data.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def get_conn(db_path: Path | str | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path | str | None = None) -> Path:
    path = Path(db_path) if db_path else DB_PATH
    conn = get_conn(path)
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        conn.executescript(f.read())
    migrate(conn)
    conn.commit()
    conn.close()
    return path


def migrate(conn: sqlite3.Connection) -> None:
    """Agrega columnas/tablas nuevas a DBs ya creadas (sin borrar datos)."""
    wanted: dict[str, list[tuple[str, str]]] = {
        "videos": [
            ("beat_key", "TEXT"),
            ("tags", "TEXT DEFAULT ''"),
            ("tags_count", "INTEGER DEFAULT 0"),
            ("description_len", "INTEGER DEFAULT 0"),
            ("views_per_day", "REAL DEFAULT 0"),
            ("engagement_rate", "REAL DEFAULT 0"),
            ("seo_score", "INTEGER DEFAULT 0"),
            ("category_id", "TEXT DEFAULT ''"),
        ],
        "beatstars_sales": [("beat_key", "TEXT")],
        "channels": [("description", "TEXT DEFAULT ''"), ("thumbnail_url", "TEXT DEFAULT ''")],
    }
    for tbl, cols in wanted.items():
        existing = {r[1] for r in conn.execute(f"PRAGMA table_info({tbl})")}
        for name, ddl in cols:
            if name not in existing:
                conn.execute(f"ALTER TABLE {tbl} ADD COLUMN {name} {ddl}")
    # Tablas nuevas (CREATE IF NOT EXISTS, no borra nada)
    conn.execute("""CREATE TABLE IF NOT EXISTS traffic_sources (
      snapshot_date TEXT NOT NULL, source TEXT NOT NULL,
      views INTEGER DEFAULT 0, watch_minutes REAL DEFAULT 0,
      PRIMARY KEY (snapshot_date, source))""")
    conn.execute("""CREATE TABLE IF NOT EXISTS device_views (
      snapshot_date TEXT NOT NULL, device TEXT NOT NULL,
      views INTEGER DEFAULT 0, watch_minutes REAL DEFAULT 0,
      PRIMARY KEY (snapshot_date, device))""")
    conn.execute("""CREATE TABLE IF NOT EXISTS search_terms (
      snapshot_date TEXT NOT NULL, term TEXT NOT NULL,
      views INTEGER DEFAULT 0, PRIMARY KEY (snapshot_date, term))""")
    conn.execute("""CREATE TABLE IF NOT EXISTS demographics (
      snapshot_date TEXT NOT NULL, age_group TEXT NOT NULL, gender TEXT NOT NULL,
      views INTEGER DEFAULT 0, watch_minutes REAL DEFAULT 0,
      PRIMARY KEY (snapshot_date, age_group, gender))""")
    conn.execute("""CREATE TABLE IF NOT EXISTS video_impressions (
      video_id TEXT NOT NULL, snapshot_date TEXT NOT NULL,
      views_28d INTEGER DEFAULT 0, impressions_28d INTEGER DEFAULT 0, ctr_28d REAL DEFAULT 0,
      PRIMARY KEY (video_id, snapshot_date))""")
    # Vista de velocidad real
    conn.execute("DROP VIEW IF EXISTS v_video_velocity")
    conn.execute("""CREATE VIEW v_video_velocity AS
      WITH r AS (
        SELECT video_id, snapshot_date, views,
          LAG(views) OVER (PARTITION BY video_id ORDER BY snapshot_date) AS prev_views,
          LAG(snapshot_date) OVER (PARTITION BY video_id ORDER BY snapshot_date) AS prev_date
        FROM video_metrics_snapshots)
      SELECT video_id, snapshot_date, views,
        COALESCE(views - prev_views, 0) AS views_gain,
        COALESCE(julianday(snapshot_date) - julianday(prev_date), 0) AS days_diff,
        CASE WHEN COALESCE(julianday(snapshot_date) - julianday(prev_date), 0) > 0
             THEN (views - prev_views) / (julianday(snapshot_date) - julianday(prev_date))
             ELSE 0 END AS views_per_day_real
      FROM r WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM video_metrics_snapshots)""")
