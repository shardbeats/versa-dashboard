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
    """Agrega columnas nuevas a DBs ya creadas (sin borrar datos)."""
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
