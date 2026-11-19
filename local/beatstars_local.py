"""Import BeatStars CSV -> SQLite."""
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

from src.transform.beatstars import clean_beatstars_sales, validate_beatstars_sales
from .db import get_conn
from .matching import beat_key


def normalize_product_name(name: str) -> str:
    """Quita el sufijo de licencia '| Buy 1 get 1 free...' para matchear con YouTube."""
    s = str(name).split("|")[0].strip()
    return s.strip("\"' ").strip()


def import_beatstars_csv(csv_path: str | Path, db_path=None):
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"No existe CSV: {csv_path}")

    # El export original tiene 6 filas de header
    try:
        raw = pd.read_csv(csv_path, skiprows=6)
    except Exception:
        raw = pd.read_csv(csv_path)

    df = clean_beatstars_sales(raw)
    validate_beatstars_sales(df)

    conn = get_conn(db_path)
    cur = conn.cursor()
    now_iso = datetime.now(timezone.utc).isoformat()

    # El CSV es un resumen agregado completo -> reemplazar, no duplicar.
    cur.execute("DELETE FROM beatstars_sales")

    n = 0
    for _, r in df.iterrows():
        product = normalize_product_name(r.get("product_name", ""))
        if not product:
            continue
        cur.execute(
            """INSERT INTO beatstars_sales
               (product_name, beat_key, product_type, quantity, gross_amount, discounts,
                collab_amount, beatstars_fee, net_revenue, imported_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                product,
                beat_key(product),
                str(r.get("product_type", "")),
                float(r.get("quantity", 1) or 0),
                float(r.get("gross_amount", 0) or 0),
                float(r.get("discounts", 0) or 0),
                float(r.get("collab_amount", 0) or 0),
                float(r.get("beatstars_fee", 0) or 0),
                float(r.get("net_revenue", 0) or 0),
                now_iso,
            ),
        )
        n += 1

    conn.commit()
    conn.close()
    print(f"\nOK BeatStars -> SQLite: {n} ventas desde {csv_path}")
    return n
