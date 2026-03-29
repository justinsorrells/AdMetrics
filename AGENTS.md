# AdMetrics — Codex Build Instructions

Build a REST API for advertising campaign metric aggregation and reporting.
This is a portfolio project for a software engineering internship application at Mediaocean.

## What to build

A FastAPI application that ingests advertising campaign performance data (impressions, clicks, spend, conversions) via REST endpoints, stores it in SQLite, and exposes aggregation and comparison endpoints. Designed to mirror the kind of data pipeline and API work done in ad-tech platforms.

## Tech stack

- Python 3.11+
- FastAPI (REST API)
- SQLite via SQLAlchemy (ORM, not raw SQL)
- Pydantic v2 (request/response models)
- pandas (aggregation logic)
- pytest + httpx (API testing)
- Docker + docker-compose

## Project structure

```
admetrics/
  api/
    main.py           # FastAPI app
    routes/
      campaigns.py    # CRUD for campaigns
      metrics.py      # Ingest daily metric rows
      reports.py      # Aggregated reports + comparisons
      health.py       # GET /health
  db/
    models.py         # Campaign, DailyMetric SQLAlchemy models
    session.py        # DB session
  services/
    aggregator.py     # pandas-based rollup logic
  schemas/
    campaign.py       # Pydantic schemas
    metric.py
    report.py
  config.py           # pydantic-settings
tests/
  test_campaigns.py
  test_metrics.py
  test_reports.py
Dockerfile
docker-compose.yml
requirements.txt
README.md
seed_data.py          # Script to seed realistic fake campaign data
```

## MVP endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /campaigns | Create a campaign (name, advertiser, budget, start/end date) |
| GET | /campaigns | List all campaigns |
| GET | /campaigns/{id} | Get single campaign |
| POST | /campaigns/{id}/metrics | Ingest a daily metric row (date, impressions, clicks, spend, conversions) |
| GET | /campaigns/{id}/report | Aggregated totals + CTR + CPA for the campaign |
| GET | /reports/compare | Compare two campaigns side-by-side (query params: a=id&b=id) |
| GET | /health | Liveness check |

## Key implementation details

- Computed fields: CTR = clicks/impressions, CPA = spend/conversions (handle div-by-zero)
- `/report` endpoint should return: total impressions, total clicks, total spend, total conversions, CTR, CPA, best performing day
- `/reports/compare` should return both campaigns' aggregates plus a delta/winner column
- seed_data.py generates 3 sample campaigns with 30 days of realistic metric data each
- All config via pydantic-settings + .env
- Full pytest suite using httpx TestClient, no external dependencies needed in tests

## README should include

- What it does and why it's useful (ad-tech context)
- Setup instructions (venv, pip install, .env)
- Docker instructions
- Example curl commands for each endpoint
- Sample output from the /report and /compare endpoints
- How to seed the database

## Quality bar

- All endpoints have docstrings and proper HTTP status codes
- pytest coverage > 80%
- Dockerfile must build cleanly
- No hardcoded secrets
