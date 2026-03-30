"""Reporting schemas."""

from datetime import date
from typing import Literal

from pydantic import BaseModel


class DailyTrendPoint(BaseModel):
    """A single day in the report's trend series."""

    date: date
    impressions: int
    clicks: int
    spend: float
    conversions: int
    ctr: float
    cpa: float | None


class BestPerformingDay(BaseModel):
    """The strongest single day in a campaign."""

    date: date
    impressions: int
    clicks: int
    spend: float
    conversions: int
    ctr: float
    cpa: float | None


class PacingInsight(BaseModel):
    """Budget pacing information for a campaign."""

    as_of_date: date
    campaign_budget: float
    spend_to_date: float
    remaining_budget: float
    budget_utilization: float
    expected_spend_to_date: float
    pacing_ratio: float | None
    average_daily_spend: float
    projected_total_spend: float
    projected_budget_variance: float
    elapsed_days: int
    total_campaign_days: int
    pacing_status: Literal["not_started", "on_track", "underpacing", "overpacing", "complete"]


class CampaignReport(BaseModel):
    """Aggregated campaign performance summary."""

    campaign_id: int
    campaign_name: str
    advertiser: str
    report_start_date: date
    report_end_date: date
    days_in_report: int
    days_with_data: int
    total_impressions: int
    total_clicks: int
    total_spend: float
    total_conversions: int
    ctr: float
    cpa: float | None
    best_performing_day: BestPerformingDay | None
    daily_breakdown: list[DailyTrendPoint]
    pacing: PacingInsight


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
