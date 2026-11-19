# MAAM local (SQLite)

Version local del fork, sin BigQuery / dbt / Cloud. Guarda historico diario en `local/data.db`.

## 1. Instalar

```powershell
cd "D:\Proyectos programacion\Github\versa-dashboard"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r local/requirements-local.txt
```

## 2. YouTube OAuth (una vez)

1. Google Cloud Console -> APIs: habilita **YouTube Data API v3** + **YouTube Analytics API**
2. Credenciales -> OAuth client ID (Desktop) -> descarga como `client_secret.json` en la raiz del repo
3. Primera corrida abre navegador y crea `token.json`:
```powershell
python local/main_local.py youtube --max-videos 10
```

Archivos sensibles (`client_secret.json`, `token.json`, `local/data.db`) ya estan en `.gitignore` local, no se suben.

## 3. Uso diario

```powershell
# crear DB
python local/main_local.py init

# bajar stats de tu canal (canal autenticado, soporta multi-canal si cambias de cuenta)
python local/main_local.py youtube

# importar ventas BeatStars (CSV export, con 6 filas de header como original)
python local/main_local.py beatstars --csv "D:\ruta\sales_report.csv"

# ver resumen
python local/main_local.py stats
```

Tablas: `channels`, `channel_snapshots`, `videos`, `video_metrics_snapshots`, `beatstars_sales`, `country_views`.
Vistas: `v_video_latest`, `v_channel_growth`, `v_beat_cross`.

Puedes abrir `local/data.db` con DB Browser for SQLite / Datasette / Streamlit.

## Diferencias con upstream

- No BigQuery, no dbt, no Docker, no Scheduler. El snapshot diario es `INSERT OR REPLACE` por `(video_id, snapshot_date)`.
- Reusa `src/extract/youtube.py` + `src/transform/youtube.py` originales.
- Rama: `local-sqlite`. Upstream queda en `main`.
