"""MAAM local dashboard (Streamlit + SQLite)."""
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DB_PATH = Path(__file__).resolve().parent / "data.db"


@st.cache_data(ttl=60)
def q(sql: str) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    try:
        return pd.read_sql_query(sql, conn)
    finally:
        conn.close()


st.set_page_config(page_title="MAAM local", layout="wide")
st.title("MAAM local — YouTube + BeatStars")

if not DB_PATH.exists():
    st.warning("No hay data.db. Corre `run.bat` opcion 1 primero.")
    st.stop()

channels = q("SELECT channel_id, title FROM channels")
if channels.empty:
    st.warning("Sin canales. Corre `run.bat` opcion 1 primero.")
    st.stop()

chan = st.sidebar.selectbox(
    "Canal", channels["channel_id"].tolist(),
    format_func=lambda cid: channels.loc[channels.channel_id == cid, "title"].iloc[0],
)

tab1, tab2, tab3, tab4 = st.tabs(["Resumen", "Crecimiento", "Videos", "BeatStars x YT"])

with tab1:
    snaps = q(
        f"SELECT * FROM channel_snapshots WHERE channel_id='{chan}' "
        "ORDER BY snapshot_date DESC LIMIT 1"
    )
    tot_videos = q(f"SELECT COUNT(*) n FROM videos WHERE channel_id='{chan}'").iloc[0, 0]
    rev = q(
        "SELECT COALESCE(SUM(estimated_revenue),0) r FROM video_metrics_snapshots m "
        f"JOIN videos v ON v.video_id=m.video_id WHERE v.channel_id='{chan}' "
        "AND m.snapshot_date=(SELECT MAX(snapshot_date) FROM video_metrics_snapshots)"
    ).iloc[0, 0]
    c1, c2, c3, c4 = st.columns(4)
    if not snaps.empty:
        s = snaps.iloc[0]
        c1.metric("Subs", f"{s['subs']:,}")
        c2.metric("Views canal", f"{s['views']:,}")
        c3.metric("Videos", f"{tot_videos:,}")
        c4.metric("Revenue est. (lifetime)", f"${rev:,.2f}")
    else:
        st.info("Sin snapshots todavia. Corre opcion 1.")

    cross = q(
        "SELECT beat, beatstars_revenue, yt_views FROM v_beat_cross "
        "WHERE beatstars_revenue > 0 OR yt_views > 0 "
        "ORDER BY COALESCE(beatstars_revenue,0) DESC LIMIT 15"
    )
    if not cross.empty:
        st.subheader("Top beats por revenue BeatStars vs views YT")
        fig = px.bar(cross, x="beat", y=["beatstars_revenue", "yt_views"],
                     barmode="group", title="Revenue ($) vs Views")
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    growth = q(
        f"SELECT * FROM v_channel_growth WHERE channel_id='{chan}' ORDER BY snapshot_date"
    )
    if growth.empty:
        st.info("Corre opcion 1 dos dias distintos para ver crecimiento.")
    else:
        st.subheader("Subs en el tiempo")
        st.plotly_chart(px.line(growth, x="snapshot_date", y="subs"), use_container_width=True)
        st.subheader("Views en el tiempo")
        st.plotly_chart(px.line(growth, x="snapshot_date", y="views"), use_container_width=True)
        st.subheader("Delta diario")
        st.plotly_chart(px.bar(growth, x="snapshot_date", y=["subs_delta", "views_delta"],
                               barmode="group"), use_container_width=True)

with tab3:
    vids = q(
        "SELECT v.title, v.beat_name, m.views, m.likes, m.comments, "
        "m.watch_time_minutes, m.estimated_revenue "
        "FROM videos v JOIN video_metrics_snapshots m ON m.video_id=v.video_id "
        f"WHERE v.channel_id='{chan}' "
        "AND m.snapshot_date=(SELECT MAX(snapshot_date) FROM video_metrics_snapshots) "
        "ORDER BY m.views DESC LIMIT 30"
    )
    if vids.empty:
        st.info("Sin datos de videos.")
    else:
        st.subheader("Top 30 videos por views")
        st.plotly_chart(px.bar(vids.head(15), x="title", y="views", hover_data=["beat_name", "likes"]),
                        use_container_width=True)
        st.dataframe(vids, use_container_width=True)

with tab4:
    beats = q(
        "SELECT product_name, SUM(net_revenue) rev, COUNT(*) ventas "
        "FROM beatstars_sales GROUP BY 1 ORDER BY rev DESC LIMIT 30"
    )
    if beats.empty:
        st.info("Sin ventas. Importa tu CSV con opcion 2.")
    else:
        st.subheader("Top beats por revenue")
        st.plotly_chart(px.bar(beats, x="product_name", y="rev"), use_container_width=True)
        st.dataframe(beats, use_container_width=True)

    countries = q("SELECT country_code, SUM(views) views FROM country_views GROUP BY 1 ORDER BY views DESC LIMIT 20")
    if not countries.empty:
        st.subheader("Views por pais")
        st.plotly_chart(px.bar(countries, x="country_code", y="views"), use_container_width=True)
