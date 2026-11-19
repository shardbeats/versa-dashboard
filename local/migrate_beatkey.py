"""Migracion: beat_key en videos/ventas + vista cruce nueva."""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from local.matching import beat_key, extract_beat_name  # noqa: E402

conn = sqlite3.connect("local/data.db")
cur = conn.cursor()

for tbl in ("videos", "beatstars_sales"):
    cols = [r[1] for r in cur.execute(f"PRAGMA table_info({tbl})")]
    if "beat_key" not in cols:
        cur.execute(f"ALTER TABLE {tbl} ADD COLUMN beat_key TEXT DEFAULT ''")
        print(f"+ columna beat_key en {tbl}")

# Re-parsear beat_name de videos con el parser mejorado
rows = cur.execute("SELECT video_id, title FROM videos").fetchall()
n = 0
for vid, title in rows:
    bn = extract_beat_name(title)
    cur.execute("UPDATE videos SET beat_name=?, beat_key=? WHERE video_id=?",
                (bn, beat_key(bn), vid))
    n += 1
print(f"videos re-parseados: {n}")

# beat_key de ventas (normaliza nombre crudo por si acaso)
srows = cur.execute("SELECT id, product_name FROM beatstars_sales").fetchall()
m = 0
for rid, pname in srows:
    base = str(pname).split("|")[0].strip().strip("\"' ")
    cur.execute("UPDATE beatstars_sales SET product_name=?, beat_key=? WHERE id=?",
                (base, beat_key(base), rid))
    m += 1
print(f"ventas normalizadas: {m}")

cur.execute("DROP VIEW IF EXISTS v_beat_cross")
conn.commit()

schema = Path("local/schema.sql").read_text(encoding="utf-8")
start = schema.find("CREATE VIEW IF NOT EXISTS v_beat_cross")
cur.executescript(schema[start:])
conn.commit()

matched = cur.execute(
    "SELECT COUNT(*) FROM (SELECT DISTINCT beat_key FROM beatstars_sales) b "
    "WHERE b.beat_key <> '' AND EXISTS (SELECT 1 FROM videos v WHERE v.beat_key = b.beat_key)"
).fetchone()[0]
total = cur.execute("SELECT COUNT(DISTINCT beat_key) FROM beatstars_sales").fetchone()[0]
print(f"cruce: {matched}/{total} productos matchean con YouTube")
conn.close()
