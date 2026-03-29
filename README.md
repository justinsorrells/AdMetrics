# AdMetrics

AdMetrics is a FastAPI portfolio project that models a lightweight ad-tech reporting service. It ingests daily campaign performance data, stores it in SQLite, and exposes rollup and comparison endpoints similar to the reporting APIs used in advertising platforms.

## Why it is useful

Ad-tech systems routinely need to accept granular delivery data, compute campaign KPIs, and present comparison views to account teams and internal tooling. This project focuses on those core backend concerns:

- campaign metadata management
- daily metric ingestion
- pandas-based aggregation for CTR and CPA
- side-by-side campaign comparison for reporting workflows

## Tech stack

- Python 3.11+
- FastAPI
- SQLAlchemy ORM with SQLite
- Pydantic v2 and pydantic-settings
- pandas
- pytest + httpx
- Docker + docker-compose

## Project layout

```text
admetrics/
  api/
  db/
  schemas/
  services/
tests/
seed_data.py
```

## Local setup

1. Create a virtual environment and activate it.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy the example environment file and adjust it if needed:

```bash
cp .env.example .env
```

4. Start the API:

```bash
uvicorn admetrics.api.main:app --reload
```

The default database is `sqlite:///./admetrics.db`.

## Docker

Build and run the API with Docker Compose:

```bash
docker compose up --build
```

The API will be available at [http://localhost:8000](http://localhost:8000).

## Endpoints

### Health

```bash
curl http://localhost:8000/health
```

### Create a campaign

```bash
curl -X POST http://localhost:8000/campaigns \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Spring Awareness Push",
    "advertiser": "Acme Media",
    "budget": 25000,
    "start_date": "2026-03-01",
    "end_date": "2026-03-31"
  }'
```

### List campaigns

```bash
curl http://localhost:8000/campaigns
```

### Get a single campaign

```bash
curl http://localhost:8000/campaigns/1
```

### Ingest a daily metric row

```bash
curl -X POST http://localhost:8000/campaigns/1/metrics \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2026-03-05",
    "impressions": 12500,
    "clicks": 540,
    "spend": 412.75,
    "conversions": 47
  }'
```

### Campaign report

```bash
curl http://localhost:8000/campaigns/1/report
```

Sample response:

```json
{
  "campaign_id": 1,
  "campaign_name": "Spring Awareness Push",
  "advertiser": "Acme Media",
  "total_impressions": 3000,
  "total_clicks": 260,
  "total_spend": 270.0,
  "total_conversions": 32,
  "ctr": 0.0867,
  "cpa": 8.44,
  "best_performing_day": {
    "date": "2026-03-02",
    "impressions": 2000,
    "clicks": 160,
    "spend": 150.0,
    "conversions": 22,
    "ctr": 0.08,
    "cpa": 6.82
  }
}
```

### Compare campaigns

```bash
curl "http://localhost:8000/reports/compare?a=1&b=2"
```

Sample response:

```json
{
  "campaign_a": {
    "campaign_id": 1,
    "campaign_name": "Campaign A",
    "advertiser": "Adventure Co",
    "total_impressions": 1000,
    "total_clicks": 60,
    "total_spend": 120.0,
    "total_conversions": 6,
    "ctr": 0.06,
    "cpa": 20.0,
    "best_performing_day": {
      "date": "2026-03-01",
      "impressions": 1000,
      "clicks": 60,
      "spend": 120.0,
      "conversions": 6,
      "ctr": 0.06,
      "cpa": 20.0
    }
  },
  "campaign_b": {
    "campaign_id": 2,
    "campaign_name": "Campaign B",
    "advertiser": "Adventure Co",
    "total_impressions": 1200,
    "total_clicks": 84,
    "total_spend": 100.0,
    "total_conversions": 9,
    "ctr": 0.07,
    "cpa": 11.11,
    "best_performing_day": {
      "date": "2026-03-01",
      "impressions": 1200,
      "clicks": 84,
      "spend": 100.0,
      "conversions": 9,
      "ctr": 0.07,
      "cpa": 11.11
    }
  },
  "comparisons": [
    {
      "metric": "impressions",
      "campaign_a_value": 1000,
      "campaign_b_value": 1200,
      "delta": 200.0,
      "winner": "campaign_b"
    }
  ],
  "overall_winner": "campaign_b"
}
```

## Seeding the database

Seed three campaigns with 30 days of realistic fake data each:

```bash
python seed_data.py
```

Reseed from scratch:

```bash
python seed_data.py --reset
```

## Testing

Run the test suite with coverage:

```bash
pytest --cov=admetrics --cov-report=term-missing
```

## Notes

- CTR is calculated as `clicks / impressions` and returns `0.0` when impressions are zero.
- CPA is calculated as `spend / conversions` and returns `null` when conversions are zero.
- The best performing day is chosen by highest conversions, then highest CTR, then lowest spend.
