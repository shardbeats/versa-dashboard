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
    conn.commit()
    conn.close()
    return path
