"""MAAM local dashboard estilo vidIQ/TubeBuddy (Streamlit + SQLite)."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DB_PATH = Path(__file__).resolve().parent / "data.db"


@st.cache_data(ttl=120)
def q(sql: str) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    try:
        return pd.read_sql_query(sql, conn)
    finally:
        conn.close()


def checklist(row: pd.Series, med_eng: float, med_vpd: float):
    tl = len(str(row.get("title", "")))
    desc = int(row.get("description_len", 0) or 0)
    tags = int(row.get("tags_count", 0) or 0)
    return [
        ("Titulo 30-70 caracteres", 30 <= tl <= 70, f"{tl} caracteres"),
        ("Descripcion +200 caracteres", desc >= 200, f"{desc} caracteres"),
        ("Entre 5 y 15 tags", 5 <= tags <= 15, f"{tags} tags"),
        ("Engagement sobre mediana", float(row.get("engagement_rate", 0) or 0) >= med_eng,
         f"{row.get('engagement_rate', 0)}% vs {med_eng:.2f}%"),
        ("Views/dia sobre mediana", float(row.get("views_per_day", 0) or 0) >= med_vpd,
         f"{row.get('views_per_day', 0)} vs {med_vpd:.1f}"),
    ]


st.set_page_config(page_title="MAAM local", layout="wide")
st.title("MAAM local — estilo vidIQ / TubeBuddy")

if not DB_PATH.exists():
    st.warning("No hay data.db. Corre `run.bat` opcion 1 primero.")
    st.stop()

channels = q("SELECT channel_id, title, description, thumbnail_url FROM channels")
if channels.empty:
    st.warning("Sin canales. Corre `run.bat` opcion 1 primero.")
    st.stop()

chan_id = st.sidebar.selectbox(
    "Canal", channels["channel_id"].tolist(),
    format_func=lambda cid: channels.loc[channels.channel_id == cid, "title"].iloc[0],
)
ch = channels.loc[channels.channel_id == chan_id].iloc[0]
snap = q(f"SELECT * FROM channel_snapshots WHERE channel_id='{chan_id}' ORDER BY snapshot_date DESC LIMIT 1")
vids = q(
    "SELECT v.*, m.views, m.likes, m.comments, m.watch_time_minutes, m.subs_gained, m.estimated_revenue "
    "FROM videos v LEFT JOIN video_metrics_snapshots m ON m.video_id=v.video_id "
    f"WHERE v.channel_id='{chan_id}' "
    "AND (m.snapshot_date IS NULL OR m.snapshot_date=(SELECT MAX(snapshot_date) FROM video_metrics_snapshots)) "
    "ORDER BY m.views DESC"
)

# ---- KPIs estilo TubeBuddy Channel Summary ----
c = st.columns(6)
subs = int(snap.iloc[0]["subs"]) if not snap.empty else 0
views = int(snap.iloc[0]["views"]) if not snap.empty else 0
n_vids = len(vids)
avg_views = round(vids["views"].mean(), 1) if n_vids else 0
avg_eng = round(vids["engagement_rate"].mean(), 2) if n_vids else 0
pub = pd.to_datetime(vids["published_at"], utc=True, errors="coerce") if n_vids else pd.Series([], dtype="datetime64[ns, UTC]")
last30 = int((pub >= (datetime.now(timezone.utc) - pd.Timedelta(days=30))).sum()) if n_vids else 0
for col, label, val in zip(c,
    ["Subs", "Views canal", "Videos", "Views/video prom.", "Engagement prom.", "Subidos 30d"],
    [f"{subs:,}", f"{views:,}", f"{n_vids:,}", f"{avg_views:,}", f"{avg_eng}%", f"{last30}"]):
    col.metric(label, val)

tab_score, tab_rank, tab_time, tab_tags, tab_traf, tab_aud, tab_out, tab_audit = st.tabs(
    ["Scorecard", "Rankings", "Mejor hora", "Tags", "Trafico", "Audiencia", "Outliers", "Auditoria"])

with tab_score:
    st.subheader("Video Scorecard (estilo vidIQ)")
    if vids.empty:
        st.info("Sin videos.")
    else:
        opts = vids["video_id"].tolist()
        labels = {vid: f"{vids.loc[vids.video_id == vid, 'views'].iloc[0]:,.0f} views | "
                       f"{str(vids.loc[vids.video_id == vid, 'title'].iloc[0])[:70]}" for vid in opts}
        sel = st.selectbox("Video", opts, format_func=lambda v: labels[v])
        row = vids.loc[vids.video_id == sel].iloc[0]
        med_eng = float(vids["engagement_rate"].median())
        med_vpd = float(vids["views_per_day"].median())
        checks = checklist(row, med_eng, med_vpd)
        score = sum(1 for _, ok, _ in checks if ok) * 20

        left, right = st.columns([1, 2])
        with left:
            st.metric("SEO Score", f"{score}/100")
            st.metric("Views", f"{row['views']:,.0f}")
            st.metric("Views/dia (VPH aprox)", f"{row['views_per_day']}")
            st.metric("Engagement", f"{row['engagement_rate']}%")
            st.metric("Watch time (min)", f"{row['watch_time_minutes']:,.0f}")
        with right:
            for name, ok, detail in checks:
                st.write(("✅ " if ok else "❌ ") + f"**{name}** — {detail}")
            st.caption(f"Tags ({int(row['tags_count'] or 0)}): {(row['tags'] or '')[:300]}")

with tab_rank:
    st.subheader("Rankings (estilo TubeBuddy Videolytics)")
    if vids.empty:
        st.info("Sin datos.")
    else:
        f = st.text_input("Buscar titulo")
        df = vids.copy()
        if f:
            df = df[df["title"].str.contains(f, case=False, na=False)]
        show = df[["title", "views", "views_per_day", "likes", "comments",
                    "engagement_rate", "tags_count", "description_len", "seo_score"]].copy()
        st.dataframe(show, use_container_width=True, column_config={
            "seo_score": st.column_config.ProgressColumn("SEO", min_value=0, max_value=100),
            "engagement_rate": st.column_config.NumberColumn("Eng %", format="%.2f"),
        })
        st.caption("Tip: ordena por views_per_day para ver que sigue jalando (VPH), no solo historicos.")

with tab_time:
    st.subheader("Mejor hora para publicar")
    if vids.empty or pub.isna().all():
        st.info("Sin fechas.")
    else:
        d = pd.DataFrame({"wd": pub.dt.day_name(), "h": pub.dt.hour, "v": vids["views"].fillna(0).values})
        order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        piv = d.pivot_table(index="wd", columns="h", values="v", aggfunc="count", fill_value=0).reindex(order)
        st.plotly_chart(px.imshow(piv, labels=dict(x="Hora", y="Dia", color="# subidos"),
                                  title="Cuantos subes por dia/hora"), use_container_width=True)
        avg_wd = d.groupby("wd")["v"].mean().reindex(order)
        st.plotly_chart(px.bar(avg_wd, title="Views promedio por dia de publicacion"),
                        use_container_width=True)

with tab_tags:
    st.subheader("Tags (estilo TubeBuddy Tag Explorer)")
    if vids.empty or int(vids["tags_count"].sum()) == 0:
        st.info("Sin tags (re-corre opcion 1 para traerlos).")
    else:
        all_tags = ",".join(vids["tags"].fillna("")).split(",")
        t = pd.Series([x.strip() for x in all_tags if x.strip()]).value_counts().head(25)
        st.plotly_chart(px.bar(t, title="Tags mas usados"), use_container_width=True)
        st.caption(f"Promedio de tags por video: {vids['tags_count'].mean():.1f} "
                   "(vidIQ sugiere 5-15)")

with tab_traf:
    st.subheader("De donde viene la vista (28d)")
    traf = q("SELECT * FROM traffic_sources WHERE snapshot_date=(SELECT MAX(snapshot_date) FROM traffic_sources)")
    dev = q("SELECT * FROM device_views WHERE snapshot_date=(SELECT MAX(snapshot_date) FROM device_views)")
    search = q("SELECT * FROM search_terms WHERE snapshot_date=(SELECT MAX(snapshot_date) FROM search_terms) ORDER BY views DESC LIMIT 20")
    imp = q("SELECT video_id, views_28d, impressions_28d, ctr_28d FROM video_impressions WHERE snapshot_date=(SELECT MAX(snapshot_date) FROM video_impressions)")
    if traf.empty and dev.empty and imp.empty:
        st.info("Sin analytics profundo. Corre `run.bat` → opcion youtube, o `python local/main_local.py analytics`.")
    else:
        if not traf.empty:
            st.plotly_chart(px.pie(traf, names="source", values="views", title="Views por fuente de trafico (28d)"),
                            use_container_width=True)
            st.dataframe(traf, use_container_width=True)
        if not dev.empty:
            st.plotly_chart(px.bar(dev, x="device", y="views", title="Views por dispositivo (28d)"),
                            use_container_width=True)
        if not search.empty:
            st.subheader("Que buscan para encontrarte (28d)")
            st.plotly_chart(px.bar(search, x="views", y="term", orientation="h", title="Top terminos de busqueda"),
                            use_container_width=True)
        if not imp.empty:
            has_ctr = float(imp["ctr_28d"].fillna(0).max()) > 0
            top28 = imp.merge(vids[["video_id", "title"]], on="video_id", how="left").sort_values("views_28d", ascending=False).head(15)
            st.subheader("Top videos 28d (velocidad real)")
            st.dataframe(top28[["title", "views_28d"]], use_container_width=True)
            if has_ctr:
                st.subheader("CTR vs Views (28d, estilo vidIQ)")
                sc = imp.merge(vids[["video_id", "title"]], on="video_id", how="left")
                st.plotly_chart(px.scatter(sc, x="impressions_28d", y="views_28d", size="ctr_28d",
                                           hover_data=["title", "ctr_28d"],
                                           labels={"impressions_28d": "Impresiones", "views_28d": "Views 28d", "ctr_28d": "CTR"},
                                           title="Impresiones vs Views (tamano = CTR)"), use_container_width=True)
                low_ctr = sc[(sc["impressions_28d"] >= 1000) & (sc["ctr_28d"] < 0.03)].sort_values("impressions_28d", ascending=False).head(10)
                if not low_ctr.empty:
                    st.warning("Miniaturas a mejorar (muchas impresiones, CTR < 3%):")
                    st.dataframe(low_ctr[["title", "impressions_28d", "views_28d", "ctr_28d"]], use_container_width=True)
            else:
                st.caption("Nota: YouTube saco CTR/impresiones de la API en vivo (solo bulk Reporting API con 48h retraso). Arriba tienes views 28d reales por video.")

with tab_aud:
    st.subheader("Quien te ve (28d)")
    demo = q("SELECT * FROM demographics WHERE snapshot_date=(SELECT MAX(snapshot_date) FROM demographics)")
    ctry = q("SELECT * FROM country_views WHERE snapshot_date=(SELECT MAX(snapshot_date) FROM country_views) ORDER BY views DESC LIMIT 15")
    if demo.empty and ctry.empty:
        st.info("Sin datos de audiencia. Corre analytics.")
    else:
        if not demo.empty:
            st.caption("La API solo da % de viewers logueados (viewerPercentage), no views crudos.")
            piv = demo.pivot_table(index="age_group", columns="gender", values="views", fill_value=0)
            st.plotly_chart(px.imshow(piv, labels=dict(x="Genero", y="Edad", color="Views"),
                                      title="Views por edad/genero (28d)"), use_container_width=True)
            st.dataframe(demo, use_container_width=True)
        if not ctry.empty:
            st.plotly_chart(px.bar(ctry, x="country_code", y="views", title="Top paises"),
                            use_container_width=True)

with tab_out:
    st.subheader("Outliers + velocidad real (estilo vidIQ)")
    vel = q("SELECT * FROM v_video_velocity")
    imp28 = q("SELECT video_id, views_28d, impressions_28d, ctr_28d FROM video_impressions WHERE snapshot_date=(SELECT MAX(snapshot_date) FROM video_impressions)")
    if vids.empty:
        st.info("Sin videos.")
    else:
        base = vids[["video_id", "title", "views", "views_per_day"]].copy()
        if not vel.empty:
            base = base.merge(vel[["video_id", "views_gain", "days_diff", "views_per_day_real"]], on="video_id", how="left")
        else:
            base["views_gain"] = 0
            base["days_diff"] = 0
            base["views_per_day_real"] = 0
        base[["views_gain", "days_diff", "views_per_day_real"]] = base[["views_gain", "days_diff", "views_per_day_real"]].fillna(0)
        has_hist = (base["days_diff"] > 0).any()
        # Preferir views 28d reales de Analytics (views_28d/28) sobre snapshot diff
        if not imp28.empty and int(imp28["views_28d"].fillna(0).sum()) > 0:
            base = base.merge(imp28[["video_id", "views_28d"]], on="video_id", how="left")
            base["views_28d"] = base["views_28d"].fillna(0)
            base["vel"] = (base["views_28d"] / 28).round(1)
            src = "real 28d (Analytics)"
        else:
            base["vel"] = base["views_per_day_real"].where(has_hist, base["views_per_day"])
            src = "real, entre snapshots" if has_hist else "aprox: views/edad, corre 2 dias para velocidad real"
        med = float(base["vel"].median())
        denom = med if med != 0 else 1.0
        base["outlier_x"] = (base["vel"] / denom).round(1)
        st.caption(f"Mediana velocidad: {med:.1f} views/dia ({src})")
        top = base.sort_values("vel", ascending=False).head(15)
        st.plotly_chart(px.bar(top, x="title", y="vel", hover_data=["views", "outlier_x"],
                               labels={"vel": "Views/dia", "title": ""},
                               title="Top velocidad (VPH)"), use_container_width=True)
        out = base[base["outlier_x"] >= 3].sort_values("outlier_x", ascending=False)
        if out.empty:
            st.info("Aun no hay outliers (3x sobre la mediana). Con 2+ dias de datos aparecen solos.")
        else:
            st.success(f"{len(out)} outliers (>=3x mediana):")
            st.dataframe(out[["title", "views", "vel", "outlier_x"]], use_container_width=True)
        if not imp28.empty:
            st.caption("Cruza con CTR: un outlier con CTR alto = formato/miniatura ganadora, repitelo.")

with tab_audit:
    st.subheader("Auditoria del canal (estilo vidIQ Audit)")
    items = []
    items.append(("Descripcion del canal completa (+100)", len(str(ch.get("description", ""))) >= 100,
                  f"{len(str(ch.get('description', '')))} caracteres"))
    items.append(("Subiendo consistente (3+ videos / 30d)", last30 >= 3, f"{last30} en 30d"))
    if n_vids:
        pct_tags = (vids["tags_count"] >= 5).mean() * 100
        pct_desc = (vids["description_len"] >= 200).mean() * 100
        items.append(("80%+ videos con 5+ tags", pct_tags >= 80, f"{pct_tags:.0f}%"))
        items.append(("80%+ videos con descripcion larga", pct_desc >= 80, f"{pct_desc:.0f}%"))
        shorts = int(vids["is_short"].sum())
        items.append(("Mezcla Shorts/Long (info)", True, f"{shorts} shorts / {n_vids - shorts} largos"))
    for name, ok, detail in items:
        st.write(("✅ " if ok else "⚠️ ") + f"**{name}** — {detail}")
