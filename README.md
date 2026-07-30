# MAAM

<p align="center">
  <strong>Music Analytics & Asset Management</strong><br>
  An end-to-end data engineering project for combining YouTube Analytics and BeatStars sales into a unified analytics platform.
</p>

---

## Overview

MAAM is an end-to-end data engineering project built to automate the collection, transformation, modeling and visualization of music business data.

The project extracts data from multiple sources, cleans and validates it, builds analytical data models in BigQuery, and presents cross-platform insights through an interactive  Studio dashboard.

Rather than focusing only on visualization, MAAM emphasizes data engineering concepts such as ETL pipelines, dimensional modeling, data quality, business rules, and cross-platform entity matching.

---

## Dashboard

![MAAM Dashboard](docs/maam-dashboard.jpg)

---

## Features

- YouTube Data API integration
- YouTube Analytics API integration
- BeatStars sales ingestion
- Automated ETL pipeline
- Bronze / Silver / Gold architecture
- Star schema data model
- Cross-platform beat matching
- Manual business rules for edge cases
- Country-level audience analytics
- Interactive Google Data Studio dashboard

---

## Architecture

```
YouTube Data API        YouTube Analytics API        BeatStars CSV Export
        │                        │                            │
        └────────────────────────┴────────────────────────────┘
                                 │
                                 ▼
                        Python ETL Pipeline
                 Extract → Clean → Validate → Transform
                                 │
                                 ▼
                         Local Silver Parquet
                                 │
                                 ▼
                         Google BigQuery
                       ┌─────────┴─────────┐
                       │                   │
                       ▼                   ▼
                 Silver Datasets      Gold Datasets
                                      SQL transformations,
                                      matching rules and
                                      analytical models
                                             │
                                             ▼
                                  Google Data Studio Dashboard
```

---

## Data Model

### Silver Layer

- `dim_youtube_video`
- `fact_youtube_video_metrics`
- `sales_summary`

### Gold Layer

- `youtube_video_performance`
- `beatstars_sales_performance`
- `dim_beat`
- `cross_platform_beat_performance`
- `youtube_country_performance`
- `beatstars_matching_rules`

---

## Engineering Challenges

### Cross-platform Matching

BeatStars products and YouTube videos do not share a common identifier.

MAAM resolves this by combining normalized beat names, business rules and manual matching where necessary.

---

### Duplicate Product Names

Different BeatStars products can legitimately share the same product name.

Instead of forcing incorrect joins, MAAM detects ambiguous matches and isolates them until explicit business rules are provided.

---

### Manual Matching Rules

Some historical edge cases require deterministic matching.

Examples include:

- Walk My Choppa
- In My Cup

These are handled through a dedicated `beatstars_matching_rules` layer instead of hardcoded SQL logic.

---

## Technologies

- Python
- Pandas
- Google BigQuery
- Google Cloud Platform
- YouTube Data API
- YouTube Analytics API
- Google Data Studio
- Git
- GitHub

---

## Project Structure

```
src/
│
├── extract/
├── transform/
├── load/
│
main.py

README.md
```

---

## Requirements

This project uses private YouTube Analytics data, private BeatStars sales exports and a personal Google Cloud project.

The repository is intended to demonstrate the design and implementation of an end-to-end data engineering solution.

To run the pipeline yourself, you would need:

- Your own Google Cloud project
- OAuth credentials (`client_secret.json`)
- YouTube Data API enabled
- YouTube Analytics API enabled
- A BeatStars sales export (CSV)
- A BigQuery dataset

---

The commands below assume that the required credentials, source data and Google Cloud resources have already been configured.

## Running the Pipeline

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Run the complete ETL pipeline:

```powershell
python main.py
```

---

## Future Improvements

Version 2 may include:

- Spotify integration
- Instagram integration
- Time-series analytics
- Automated reporting
- AI-generated insights

---

## Version

Current release:

**MAAM v1.0**