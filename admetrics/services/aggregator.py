"""Aggregation helpers built on top of pandas."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from admetrics.db.models import Campaign, DailyMetric
from admetrics.schemas.report import BestPerformingDay, CampaignComparison, CampaignReport, ComparisonMetric


def _round_currency(value: float | None) -> float | None:
    """Round currency-like values to two decimals."""

    if value is None:
        return None
    return round(float(value), 2)


def _round_rate(value: float) -> float:
    """Round rate values to four decimals."""

    return round(float(value), 4)


def _safe_rate(numerator: float, denominator: float) -> float:
    """Return a zero-safe ratio for rate calculations."""

    if denominator == 0:
        return 0.0
    return numerator / denominator


def _safe_cpa(spend: float, conversions: float) -> float | None:
    """Return cost per acquisition, or None when undefined."""

    if conversions == 0:
        return None
    return spend / conversions


def aggregate_campaign(campaign: Campaign, metrics: Sequence[DailyMetric]) -> CampaignReport:
    """Aggregate campaign metrics into a report model."""

    if not metrics:
        return CampaignReport(
            campaign_id=campaign.id,
            campaign_name=campaign.name,
            advertiser=campaign.advertiser,
            total_impressions=0,
            total_clicks=0,
            total_spend=0.0,
            total_conversions=0,
            ctr=0.0,
            cpa=None,
            best_performing_day=None,
        )

    frame = pd.DataFrame(
        [
            {
                "date": metric.date,
                "impressions": metric.impressions,
                "clicks": metric.clicks,
                "spend": metric.spend,
                "conversions": metric.conversions,
            }
            for metric in metrics
        ]
    )
    frame["ctr"] = frame.apply(lambda row: _safe_rate(row["clicks"], row["impressions"]), axis=1)
    frame["cpa"] = frame.apply(lambda row: _safe_cpa(row["spend"], row["conversions"]), axis=1)
    best_row = frame.sort_values(
        by=["conversions", "ctr", "spend", "date"],
        ascending=[False, False, True, True],
    ).iloc[0]

    total_impressions = int(frame["impressions"].sum())
    total_clicks = int(frame["clicks"].sum())
    total_spend = float(frame["spend"].sum())
    total_conversions = int(frame["conversions"].sum())

    best_performing_day = BestPerformingDay(
        date=best_row["date"],
        impressions=int(best_row["impressions"]),
        clicks=int(best_row["clicks"]),
        spend=_round_currency(best_row["spend"]) or 0.0,
        conversions=int(best_row["conversions"]),
        ctr=_round_rate(best_row["ctr"]),
        cpa=_round_currency(best_row["cpa"]),
    )

    return CampaignReport(
        campaign_id=campaign.id,
        campaign_name=campaign.name,
        advertiser=campaign.advertiser,
        total_impressions=total_impressions,
        total_clicks=total_clicks,
        total_spend=_round_currency(total_spend) or 0.0,
        total_conversions=total_conversions,
        ctr=_round_rate(_safe_rate(total_clicks, total_impressions)),
        cpa=_round_currency(_safe_cpa(total_spend, total_conversions)),
        best_performing_day=best_performing_day,
    )


def compare_campaigns(report_a: CampaignReport, report_b: CampaignReport) -> CampaignComparison:
    """Compare two campaign reports side by side."""

    metric_definitions = [
        ("impressions", report_a.total_impressions, report_b.total_impressions, True),
        ("clicks", report_a.total_clicks, report_b.total_clicks, True),
        ("spend", report_a.total_spend, report_b.total_spend, False),
        ("conversions", report_a.total_conversions, report_b.total_conversions, True),
        ("ctr", report_a.ctr, report_b.ctr, True),
        ("cpa", report_a.cpa, report_b.cpa, False),
    ]

    comparisons: list[ComparisonMetric] = []
    wins_a = 0
    wins_b = 0

    for metric_name, value_a, value_b, higher_is_better in metric_definitions:
        if value_a == value_b:
            winner = "tie"
        elif value_a is None:
            winner = "campaign_b"
        elif value_b is None:
            winner = "campaign_a"
        elif (value_b > value_a and higher_is_better) or (value_b < value_a and not higher_is_better):
            winner = "campaign_b"
        else:
            winner = "campaign_a"

        if winner == "campaign_a":
            wins_a += 1
        elif winner == "campaign_b":
            wins_b += 1

        delta = None
        if value_a is not None and value_b is not None:
            delta = float(value_b) - float(value_a)
            delta = _round_rate(delta) if metric_name == "ctr" else _round_currency(delta)

        comparisons.append(
            ComparisonMetric(
                metric=metric_name,
                campaign_a_value=value_a,
                campaign_b_value=value_b,
                delta=delta,
                winner=winner,
            )
        )

    overall_winner = "tie"
    if wins_a > wins_b:
        overall_winner = "campaign_a"
    elif wins_b > wins_a:
        overall_winner = "campaign_b"

    return CampaignComparison(
        campaign_a=report_a,
        campaign_b=report_b,
        comparisons=comparisons,
        overall_winner=overall_winner,
    )
