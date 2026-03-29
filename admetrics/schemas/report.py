"""Reporting schemas."""

from datetime import date
from typing import Literal

from pydantic import BaseModel


class BestPerformingDay(BaseModel):
    """The strongest single day in a campaign."""

    date: date
    impressions: int
    clicks: int
    spend: float
    conversions: int
    ctr: float
    cpa: float | None


class CampaignReport(BaseModel):
    """Aggregated campaign performance summary."""

    campaign_id: int
    campaign_name: str
    advertiser: str
    total_impressions: int
    total_clicks: int
    total_spend: float
    total_conversions: int
    ctr: float
    cpa: float | None
    best_performing_day: BestPerformingDay | None


class ComparisonMetric(BaseModel):
    """Side-by-side metric comparison for two campaigns."""

    metric: str
    campaign_a_value: int | float | None
    campaign_b_value: int | float | None
    delta: float | None
    winner: Literal["campaign_a", "campaign_b", "tie"]


class CampaignComparison(BaseModel):
    """Comparison response between two campaign reports."""

    campaign_a: CampaignReport
    campaign_b: CampaignReport
    comparisons: list[ComparisonMetric]
    overall_winner: Literal["campaign_a", "campaign_b", "tie"]
