"""Seed the database with realistic-looking campaign data."""

from __future__ import annotations

import argparse
import random
from datetime import date, timedelta

from admetrics.config import get_settings
from admetrics.db import models  # noqa: F401
from admetrics.db.models import Campaign, DailyMetric
from admetrics.db.session import DatabaseSessionManager


def build_seed_campaigns() -> list[dict[str, object]]:
    """Return baseline campaign metadata for seeding."""

    return [
        {
            "name": "Spring Streaming Push",
            "advertiser": "Acme Media",
            "budget": 25000.0,
            "start_date": date(2026, 2, 1),
            "end_date": date(2026, 3, 2),
        },
        {
            "name": "Retail Search Lift",
            "advertiser": "Northwind Retail",
            "budget": 18000.0,
            "start_date": date(2026, 2, 10),
            "end_date": date(2026, 3, 11),
        },
        {
            "name": "Travel Awareness Burst",
            "advertiser": "Skyline Travel",
            "budget": 32000.0,
            "start_date": date(2026, 1, 20),
            "end_date": date(2026, 2, 18),
        },
    ]


def generate_daily_metrics(campaign_id: int, start_date: date, days: int) -> list[DailyMetric]:
    """Create 30 days of plausible advertising metrics."""

    metrics: list[DailyMetric] = []
    base_impressions = random.randint(9000, 18000)
    base_ctr = random.uniform(0.018, 0.055)
    base_conversion_rate = random.uniform(0.08, 0.18)
    cpm = random.uniform(7.5, 18.0)

    for day_index in range(days):
        current_date = start_date + timedelta(days=day_index)
        weekday_multiplier = 1.12 if current_date.weekday() in {1, 2, 3} else 0.94
        trend_multiplier = 1 + (day_index / (days * 25))
        impressions = int(base_impressions * weekday_multiplier * trend_multiplier * random.uniform(0.85, 1.15))
        clicks = int(impressions * base_ctr * random.uniform(0.9, 1.1))
        conversions = int(clicks * base_conversion_rate * random.uniform(0.8, 1.2))
        spend = round((impressions / 1000) * cpm * random.uniform(0.92, 1.08), 2)

        metrics.append(
            DailyMetric(
                campaign_id=campaign_id,
                date=current_date,
                impressions=impressions,
                clicks=min(clicks, impressions),
                spend=spend,
                conversions=min(conversions, clicks),
            )
        )

    return metrics


def main(reset: bool) -> None:
    """Seed sample campaigns and metric rows."""

    random.seed(42)
    settings = get_settings()
    session_manager = DatabaseSessionManager(settings.database_url)
    session_manager.create_tables()

    with session_manager.session_factory() as session:
        if reset:
            session.query(DailyMetric).delete()
            session.query(Campaign).delete()
            session.commit()

        if session.query(Campaign).count() > 0 and not reset:
            print("Database already contains campaign data. Use --reset to reseed.")
            return

        campaigns: list[Campaign] = []
        for campaign_payload in build_seed_campaigns():
            campaign = Campaign(**campaign_payload)
            session.add(campaign)
            campaigns.append(campaign)

        session.commit()
        for campaign in campaigns:
            session.refresh(campaign)
            session.add_all(generate_daily_metrics(campaign.id, campaign.start_date, 30))

        session.commit()
        print(f"Seeded {len(campaigns)} campaigns with 30 daily metric rows each.")

    session_manager.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the AdMetrics database")
    parser.add_argument("--reset", action="store_true", help="Delete existing data before seeding")
    args = parser.parse_args()
    main(reset=args.reset)
