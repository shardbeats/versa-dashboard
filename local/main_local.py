"""MAAM local: YouTube + BeatStars -> SQLite. Sin BigQuery, sin dbt, sin cloud."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from local.db import DB_PATH, init_db, get_conn  # noqa: E402


def cmd_init(args):
    path = init_db(args.db or DB_PATH)
    print(f"DB lista en {path}")


def cmd_youtube(args):
    from local.yt_local import run_youtube_local  # lazy: necesita pandas + google

    init_db(args.db or DB_PATH)
    run_youtube_local(db_path=args.db, max_videos=args.max_videos)


def cmd_beatstars(args):
    from local.beatstars_local import import_beatstars_csv  # lazy

    init_db(args.db or DB_PATH)
    import_beatstars_csv(args.csv, db_path=args.db)


def cmd_stats(args):
    conn = get_conn(args.db)
    cur = conn.cursor()
    print("\n== canales ==")
    for r in cur.execute(
        "SELECT channel_id, title FROM channels"
    ).fetchall():
        print(f"- {r['title']} [{r['channel_id']}]")
        for s in cur.execute(
            "SELECT * FROM channel_snapshots WHERE channel_id=? ORDER BY snapshot_date DESC LIMIT 5",
            (r["channel_id"],),
        ).fetchall():
            print(f"  {s['snapshot_date']}: subs={s['subs']} views={s['views']} videos={s['video_count']}")

    print("\n== top videos (ultimo snapshot) ==")
    for r in cur.execute(
        """SELECT v.title, m.views, m.likes FROM v_video_latest v
           JOIN video_metrics_snapshots m ON m.video_id=v.video_id
           ORDER BY m.views DESC LIMIT 10"""
    ).fetchall():
        print(f"- {r['views']} views | {r['title'][:80]}")

    print("\n== cruce BeatStars x YouTube (top 10) ==")
    try:
        for r in cur.execute(
            "SELECT beat, beatstars_revenue, beat_sales, yt_views FROM v_beat_cross ORDER BY beatstars_revenue DESC LIMIT 10"
        ).fetchall():
            print(f"- {r['beat'][:50]} | ${r['beatstars_revenue'] or 0:.2f} | ventas={r['beat_sales']} | yt_views={r['yt_views'] or 0}")
    except Exception as e:
        print(f"(cruce no disponible: {e})")
    conn.close()


def main():
    p = argparse.ArgumentParser(description="MAAM local SQLite")
    p.add_argument("--db", default=None, help="Ruta data.db (default local/data.db)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="Crear data.db")
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("youtube", help="Descargar stats de tu canal (OAuth)")
    s.add_argument("--max-videos", type=int, default=None)
    s.set_defaults(fn=cmd_youtube)

    s = sub.add_parser("beatstars", help="Importar CSV de BeatStars")
    s.add_argument("--csv", required=True)
    s.set_defaults(fn=cmd_beatstars)

    s = sub.add_parser("stats", help="Ver resumen local")
    s.set_defaults(fn=cmd_stats)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
