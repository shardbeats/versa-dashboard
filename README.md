# MAAM

<p align="center">
  <img src="docs/maam-logo.png" width="180">
</p>

---

# Overview

MAAM (Music Analytics & Asset Management) is an end-to-end data engineering and business intelligence project built to automate the collection, transformation, modeling and visualization of music business data.

The platform combines data from YouTube Analytics and BeatStars into a unified analytical model, allowing music producers to monitor business performance, evaluate individual beats, analyze historical trends and make data-driven pricing decisions from a single dashboard.

Rather than focusing only on visualization, MAAM emphasizes real-world data engineering concepts including ETL pipelines, dimensional modeling, data quality testing, cloud orchestration, historical snapshots, transformation with dbt, business rules, cross-platform entity matching and automated deployment.

---

# What's New in v5.0

MAAM v5.0 focuses on production automation, fresher sales ingestion and independently scheduled data workloads.

Key additions include:

- CI/CD with GitHub Actions for automated validation and deployment
- Gmail API ingestion for fresh BeatStars sales from Marketplace and Pro Page
- Independent Cloud Run Jobs with workload-specific schedules
- Latest Sales dashboard feature showing the five most recent BeatStars orders

These changes allow MAAM to process different workloads according to their individual freshness requirements instead of relying entirely on a single production schedule.

---

# Dashboard

MAAM contains three dashboard views designed for different levels of analysis.

## Home

<p align="center">
  <img src="docs/maam-dashboard-homev5.jpg">
</p>

The Home dashboard provides a quick overview of recent business and channel performance.

A dynamic period selector allows metrics to be viewed across different time windows:

- Last 7 Days
- Last 30 Days
- Last 90 Days
- Lifetime

Key metrics include:

- Total Revenue
- BeatStars Revenue
- YouTube Revenue
- Beat Sales
- Beats Published
- YouTube Views
- Subscribers Gained
- Watch Time (min)

The Home dashboard also includes a Latest Sales view showing the five most recent BeatStars orders, including beat, license type, sales channel, relative purchase time and order value.

Multi-item and promotional orders are grouped at the order level so that a single transaction is represented as one sale rather than multiple individual line items.

---

## Overview

<p align="center">
  <img src="docs/maam-dashboard.jpg">
</p>

The Overview dashboard provides a high-level view of lifetime business performance across BeatStars and YouTube.

Features include:

- BeatStars Revenue
- YouTube Revenue
- Total Sales
- Total Views
- Geographic audience distribution
- Top markets
- Best-selling beats
- Cross-platform Revenue vs Views analysis

---

## Beat Performance

<p align="center">
  <img src="docs/maam-dashboardv4.jpg">
</p>

The Beat Performance dashboard provides a detailed view of an individual beat across platforms.

Features include:

- BeatStars Revenue
- YouTube Revenue
- Beat Sales
- Beat Views
- Release Date
- Historical monthly sales
- Cross-platform performance
- Estimated Exclusive Value

The Estimated Exclusive Value model uses historical sales performance to generate a recommended price range for selling a beat exclusively.

---

# Features

- Automated ETL pipelines
- YouTube Data API integration
- YouTube Analytics API integration
- BeatStars sales export ingestion
- Gmail API sales ingestion
- Marketplace and Pro Page sales ingestion
- Bronze / Silver / Gold architecture
- BigQuery dimensional data warehouse
- dbt transformation layer
- dbt data quality tests
- Star schema modeling
- Historical YouTube metric snapshots
- Historical BeatStars sales tracking
- Dynamic time intelligence
- Latest BeatStars sales tracking
- Order-level multi-item sales modeling
- Cross-platform beat matching
- Manual business rules for edge cases
- Estimated Exclusive Value modeling
- Country-level audience analytics
- Independent Cloud Run Jobs
- Workload-specific Cloud Scheduler automation
- Secret Manager integration
- Docker containerization
- GitHub Actions CI/CD
- Automated container build and deployment
- Interactive Google Data Studio dashboard

---

# Architecture

```text
                         YouTube Data API
                                │
                         YouTube Analytics API
                                │
                                ▼
                         YouTube Pipeline
                                │
                                │
BeatStars Sales Export ──► BeatStars Pipeline
                                │
                                │
BeatStars Sales Emails ──► Gmail API
                                │
                                ▼
                     BeatStars Email Pipeline
                                │
                                ▼
                         BigQuery Silver
                                │
                                ▼
                               dbt
                     Transform → Model → Test
                                │
                                ▼
                          BigQuery Gold
                                │
                                ▼
                      Google Data Studio
                           Dashboard


Production workloads
────────────────────

Main Pipeline
    │
    └── Cloud Run Job
            │
            └── Cloud Scheduler
                    └── Daily production refresh


BeatStars Email Pipeline
    │
    └── Cloud Run Job
            │
            └── Cloud Scheduler
                    ├── 08:00
                    └── 20:00


Deployment
──────────

GitHub
   │
   ▼
GitHub Actions
   │
   ├── CI
   │
   ▼
Docker Build
   │
   ▼
Artifact Registry
   │
   ▼
Cloud Run Jobs
```

The Python pipelines are responsible for source extraction, cleaning, validation and Silver-layer loading.

YouTube and the primary BeatStars pipeline provide the core analytical datasets, while the Gmail-based BeatStars pipeline independently ingests recent sales notifications.

dbt handles analytical transformations, business logic, dimensional modeling, sales reconciliation and data quality testing in the Gold layer.

Production workloads run as containerized Google Cloud Run Jobs and are triggered independently through Cloud Scheduler according to their freshness requirements.

Changes pushed to GitHub are validated and deployed through a GitHub Actions CI/CD workflow.

---

# Data Architecture

## Silver Layer

The Silver layer contains cleaned and validated source-level data before analytical modeling.

### dim_youtube_video

YouTube video metadata including titles, beat names, publication dates and video duration.

### fact_youtube_video_metrics

Historical snapshots of cumulative YouTube performance metrics including:

- Views
- Likes
- Comments
- Watch Time
- Average View Duration
- Average View Percentage
- Subscribers Gained
- Subscribers Lost
- Estimated Revenue
- Snapshot Timestamp

### sales_summary

Cleaned BeatStars transaction-level sales data from the primary sales export, used as a source for downstream dbt models.

### stg_beatstars_email_sales

Cleaned BeatStars sales captured from Gmail notifications.

The email ingestion path provides fresher transaction data between primary BeatStars sales export refreshes and supports both Marketplace and Pro Page transactions.

---

# Historical Snapshot System

YouTube performance metrics such as views, revenue and watch time are cumulative values.

To calculate performance across rolling time periods, MAAM stores daily snapshots of these metrics instead of replacing the table during each pipeline execution.

The snapshot process follows an idempotent daily loading strategy:

```text
First run of a new day
        │
        ▼
Append daily snapshot

Additional run on same day
        │
        ▼
Replace current day's snapshot

Previous snapshots
        │
        ▼
Remain unchanged
```

This preserves historical state while preventing duplicate snapshots when the pipeline is executed multiple times on the same day.

The snapshot history provides the foundation for Dynamic Time Intelligence.

---

# dbt Transformation Layer

MAAM uses dbt to transform validated Silver data into analytics-ready Gold models.

The dbt layer is responsible for:

- Analytical transformations
- Business logic
- Cross-platform modeling
- Dimensional modeling
- Time intelligence
- Sales reconciliation
- Data quality testing
- Reusable business rules

The required dbt models are built and tested after their corresponding Silver pipelines complete.

```text
BigQuery Silver
      │
      ▼
     dbt
      │
      ├── Transform
      ├── Model
      ├── Apply business rules
      ├── Reconcile sales sources
      └── Test
      │
      ▼
BigQuery Gold
```

---

# Gold Layer

The Gold layer contains analytics-ready models consumed by the dashboard.

Current models include:

- dashboard_overview
- youtube_video_performance
- exclusive_value_estimates
- beatstars_sales_performance
- beatstars_daily_beat_sales
- beatstars_monthly_beat_sales
- cross_platform_beat_performance
- dim_beat
- homepage_time_intelligence
- latest_beatstars_sales

The Latest Sales model groups transaction items at the order level and exposes the five most recent BeatStars orders for the Home dashboard.

---

# dbt Seeds

## beatstars_matching_rules

A controlled business-rules dataset used to resolve historical cross-platform matching edge cases.

Keeping these rules as a dbt seed separates manual overrides from transformation code and makes the matching logic easier to maintain and audit.

---

# Dynamic Time Intelligence

MAAM supports dynamic analysis across multiple time windows:

- Last 7 Days
- Last 30 Days
- Last 90 Days
- Lifetime

BeatStars metrics are calculated from historical transaction dates.

YouTube metrics use differences between historical cumulative snapshots to determine performance within each period.

This allows metrics from two fundamentally different source systems to be presented through a unified time selector.

Metrics include:

- Total Revenue
- BeatStars Revenue
- YouTube Revenue
- Beat Sales
- Beats Published
- YouTube Views
- Subscribers Gained
- Watch Time (min)

---

# Latest Sales

MAAM v5.0 introduces a dedicated Latest Sales model and dashboard component.

BeatStars sales notifications are ingested through the Gmail API and processed independently from the primary production refresh.

The dashboard displays the five most recent orders with:

- Beat
- License
- Purchase time
- Marketplace or Pro Page source
- Order value

Multi-item purchases such as promotional deals are modeled at the order level. This prevents a transaction containing multiple beats from appearing as multiple separate sales in the Latest Sales view.

The underlying model retains the individual items belonging to each transaction while exposing a compact order-level representation to the dashboard.

---

# Estimated Exclusive Value

MAAM includes a data-driven model for estimating the potential exclusive sale value of an individual beat.

Instead of assigning the same exclusive price to every beat, the model uses historical performance to generate a recommended price range.

This turns historical analytics into an actionable business metric that can support pricing decisions when negotiating exclusive beat sales.

---

# Engineering Challenges

## Cross-platform Entity Matching

BeatStars products and YouTube videos do not share a common identifier.

MAAM resolves this by combining normalized beat names, deterministic matching logic and controlled manual overrides where required.

This creates a unified beat entity that can be analyzed across both platforms.

---

## Ambiguous Product Names

Different BeatStars products may legitimately share the same product name.

Automatically joining these records could assign revenue or sales to the wrong YouTube video.

Instead of creating potentially incorrect relationships, ambiguous matches are isolated until deterministic matching rules become available.

---

## Manual Matching Rules

Historical edge cases are handled through a dedicated dbt seed instead of hardcoded SQL conditions.

This keeps transformation logic clean while allowing controlled and auditable business overrides.

---

## Cumulative YouTube Metrics

The YouTube APIs provide cumulative lifetime metrics for individual videos.

This creates a challenge when calculating performance for periods such as the last 7, 30 or 90 days.

MAAM solves this by maintaining daily metric snapshots and calculating the difference between historical states.

---

## Idempotent Snapshot Loading

The production pipeline may be executed more than once during the same day.

Simply appending every execution would create duplicate daily snapshots and distort downstream calculations.

MAAM therefore replaces an existing snapshot for the current UTC date before loading the newest version while preserving all previous days.

---

## Different Source Behaviors

YouTube and BeatStars provide data in fundamentally different ways.

YouTube metrics are retrieved through APIs and contain cumulative values, while BeatStars sales are available as historical transaction data and individual sales notifications.

The Gold layer abstracts these differences and exposes consistent analytical metrics to the dashboard.

---

## Sales Freshness and Reconciliation

The primary BeatStars sales dataset provides historical transaction data but does not provide the same freshness required by features such as Latest Sales.

MAAM v5.0 introduces an independent Gmail ingestion pipeline that captures BeatStars transaction notifications and makes recent Marketplace and Pro Page sales available without waiting for the primary sales refresh.

Because the same transaction may later exist in both sources, MAAM reconciles sales using transaction identifiers to prevent the same order from being counted twice.

This allows fresh email-derived transactions to temporarily fill the gap while preserving the primary sales dataset as part of the historical pipeline.

---

## Workload-Specific Scheduling

Not every source requires the same refresh frequency.

Instead of increasing the frequency of the complete MAAM pipeline, v5.0 separates the BeatStars email workload into its own Cloud Run Job.

This allows recent sales to be refreshed independently while avoiding unnecessary execution of YouTube extraction and unrelated transformations.

---

# Data Quality

Data is validated at multiple stages of the pipeline.

Python validation is performed before Silver data is loaded into BigQuery.

The Gold transformation layer uses dbt tests to validate analytical models before the pipeline is considered successful.

Examples include:

- Required field validation
- Duplicate identifier checks
- Data type validation
- Model-level dbt tests
- Referential and business-rule validation
- Order-level uniqueness validation

A failed dbt build causes the corresponding production pipeline to fail rather than publishing an invalid analytical layer.

---

# CI/CD

MAAM v5.0 introduces a GitHub Actions CI/CD workflow.

Changes pushed to the main branch pass through automated validation before deployment.

```text
Code Change
    │
    ▼
Git Push
    │
    ▼
GitHub Actions
    │
    ├── CI / Validation
    │
    ▼
Container Build
    │
    ▼
Artifact Registry
    │
    ▼
Cloud Run Deployment
```

This reduces manual deployment steps and keeps the production Cloud Run Jobs aligned with the version-controlled codebase.

---

# Technologies

- Python
- Pandas
- SQL
- dbt
- Google BigQuery
- Google Cloud Run Jobs
- Google Cloud Scheduler
- Google Secret Manager
- Google Cloud Build
- Google Artifact Registry
- Docker
- GitHub Actions
- YouTube Data API
- YouTube Analytics API
- Gmail API
- Google Data Studio
- Git
- GitHub

---

# Project Structure

```text
versa-dashboard/
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── src/
│   ├── auth.py
│   ├── auth_gmail.py
│   │
│   ├── extract/
│   │   ├── beatstars.py
│   │   ├── beatstars_email.py
│   │   └── youtube.py
│   │
│   ├── transform/
│   │   ├── beatstars.py
│   │   ├── beatstars_email.py
│   │   └── youtube.py
│   │
│   └── load/
│       ├── beatstars.py
│       ├── beatstars_email.py
│       ├── bigquery.py
│       └── youtube.py
│
├── dbt/
│   └── maam/
│       ├── models/
│       │   └── gold/
│       │       └── latest_beatstars_sales.sql
│       │
│       ├── seeds/
│       │   └── beatstars_matching_rules.csv
│       │
│       ├── dbt_project.yml
│       └── profiles.yml
│
├── main.py
├── Dockerfile
├── requirements.txt
└── README.md
```

---

# Pipeline Execution

MAAM supports individual source workloads as well as the complete production pipeline.

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Run the complete pipeline:

```powershell
python main.py full
```

Run only the YouTube pipeline:

```powershell
python main.py youtube
```

Run only the primary BeatStars pipeline:

```powershell
python main.py beatstars
```

Run the BeatStars Gmail ingestion pipeline:

```powershell
python main.py beatstars_email
```

The production workloads are containerized with Docker and executed through Google Cloud Run Jobs.

The primary production refresh and BeatStars email ingestion run independently, allowing each workload to use a schedule appropriate to its data freshness requirements.

---

# Production Scheduling

MAAM v5.0 uses separate production schedules for different workloads.

```text
08:00  → BeatStars Email Pipeline
19:00  → Main Production Pipeline
20:00  → BeatStars Email Pipeline
```

The BeatStars email pipeline can therefore refresh recent sales without unnecessarily executing the complete MAAM pipeline.

Schedules are managed through Google Cloud Scheduler and trigger the corresponding Cloud Run Jobs.

---

# Requirements

This project uses private YouTube Analytics data, private BeatStars sales data, Gmail-based sales notifications and a personal Google Cloud project.

To run the complete project independently you will need:

- Google Cloud Project
- OAuth Credentials
- YouTube Data API
- YouTube Analytics API
- Gmail API
- BeatStars Sales Export
- BigQuery datasets
- dbt-bigquery

Sensitive credentials, OAuth tokens, customer information and private source data are excluded from version control.

---

# Roadmap

Future versions may include:

- Automated trend detection
- Performance anomaly detection
- MAAM-generated insights and notifications
- Additional music platform integrations
- Expanded pricing intelligence
- Advanced business intelligence features
- AI-assisted analytics

Example future insight:

```text
MAAM has detected an unusual increase in performance for a beat.
```

The long-term goal is to evolve MAAM from a reporting platform into an intelligent music business analytics system capable of proactively identifying meaningful changes in performance.

---

# Current Version

**MAAM v5.0**