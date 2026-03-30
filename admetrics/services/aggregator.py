"""Aggregation helpers built on top of pandas."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date

import pandas as pd

from admetrics.db.models import Campaign, DailyMetric
from admetrics.schemas.report import (
    BestPerformingDay,
    CampaignComparison,
    CampaignReport,
    ComparisonMetric,
    DailyTrendPoint,
    PacingInsight,
)


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


def _build_metric_frame(metrics: Sequence[DailyMetric]) -> pd.DataFrame:
    """Convert campaign metric rows into a pandas DataFrame."""

    if not metrics:
        return pd.DataFrame(columns=["date", "impressions", "clicks", "spend", "conversions"])

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
    frame["date"] = pd.to_datetime(frame["date"])
    return frame


def _resolve_report_window(
    campaign: Campaign,
    start_date: date | None,
    end_date: date | None,
) -> tuple[date, date]:
    """Return the effective report window for a campaign."""

    requested_start = start_date or campaign.start_date
    requested_end = end_date or campaign.end_date

    if requested_end < requested_start:
        raise ValueError("start_date must be on or before end_date")

    effective_start = max(requested_start, campaign.start_date)
    effective_end = min(requested_end, campaign.end_date)

    if effective_end < effective_start:
        raise ValueError("Requested report window does not overlap the campaign date range")

    return effective_start, effective_end


def _serialize_daily_breakdown(frame: pd.DataFrame) -> list[DailyTrendPoint]:
    """Convert a trend DataFrame into response models."""

    breakdown: list[DailyTrendPoint] = []
    for row in frame.to_dict("records"):
        day = row["date"].date() if hasattr(row["date"], "date") else row["date"]
        breakdown.append(
            DailyTrendPoint(
                date=day,
                impressions=int(row["impressions"]),
                clicks=int(row["clicks"]),
                spend=_round_currency(row["spend"]) or 0.0,
                conversions=int(row["conversions"]),
                ctr=_round_rate(row["ctr"]),
                cpa=_round_currency(row["cpa"]),
            )
        )
    return breakdown


def _build_trend_frame(
    filtered_frame: pd.DataFrame,
    report_start_date: date,
    report_end_date: date,
) -> pd.DataFrame:
    """Create a zero-filled daily trend frame for the report window."""

    date_index = pd.date_range(start=report_start_date, end=report_end_date, freq="D")
    trend_frame = pd.DataFrame({"date": date_index})

    if filtered_frame.empty:
        trend_frame["impressions"] = 0
        trend_frame["clicks"] = 0
        trend_frame["spend"] = 0.0
        trend_frame["conversions"] = 0
    else:
        trend_frame = trend_frame.merge(
            filtered_frame[["date", "impressions", "clicks", "spend", "conversions"]],
            on="date",
            how="left",
        )
        trend_frame["impressions"] = trend_frame["impressions"].fillna(0).astype(int)
        trend_frame["clicks"] = trend_frame["clicks"].fillna(0).astype(int)
        trend_frame["spend"] = trend_frame["spend"].fillna(0.0).astype(float)
        trend_frame["conversions"] = trend_frame["conversions"].fillna(0).astype(int)

    trend_frame["ctr"] = trend_frame.apply(lambda row: _safe_rate(row["clicks"], row["impressions"]), axis=1)
    trend_frame["cpa"] = trend_frame.apply(lambda row: _safe_cpa(row["spend"], row["conversions"]), axis=1)
    return trend_frame


def _build_pacing_insight(
    campaign: Campaign,
    all_metrics_frame: pd.DataFrame,
    as_of_date: date | None,
) -> PacingInsight:
    """Calculate campaign pacing against budget and elapsed days."""

    requested_as_of = as_of_date or date.today()
    total_campaign_days = (campaign.end_date - campaign.start_date).days + 1

    if requested_as_of < campaign.start_date:
        spend_to_date = 0.0
        elapsed_days = 0
        expected_spend_to_date = 0.0
        average_daily_spend = 0.0
        projected_total_spend = 0.0
        pacing_ratio = None
        pacing_status = "not_started"
        effective_as_of = requested_as_of
    else:
        effective_as_of = min(requested_as_of, campaign.end_date)
        elapsed_days = (effective_as_of - campaign.start_date).days + 1

        if all_metrics_frame.empty:
            spend_to_date = 0.0
        else:
            spend_to_date = float(
                all_metrics_frame.loc[
                    all_metrics_frame["date"] <= pd.Timestamp(effective_as_of),
                    "spend",
                ].sum()
            )

        expected_spend_to_date = campaign.budget * (elapsed_days / total_campaign_days)
        average_daily_spend = spend_to_date / elapsed_days if elapsed_days else 0.0
        projected_total_spend = average_daily_spend * total_campaign_days if elapsed_days else 0.0
        pacing_ratio = (
            _round_rate(_safe_rate(spend_to_date, expected_spend_to_date))
            if expected_spend_to_date > 0
            else None
        )

        if requested_as_of >= campaign.end_date:
            pacing_status = "complete"
        elif pacing_ratio is not None and pacing_ratio < 0.95:
            pacing_status = "underpacing"
        elif pacing_ratio is not None and pacing_ratio > 1.05:
            pacing_status = "overpacing"
        else:
            pacing_status = "on_track"

    remaining_budget = campaign.budget - spend_to_date
    projected_budget_variance = projected_total_spend - campaign.budget

    return PacingInsight(
        as_of_date=effective_as_of,
        campaign_budget=_round_currency(campaign.budget) or 0.0,
        spend_to_date=_round_currency(spend_to_date) or 0.0,
        remaining_budget=_round_currency(remaining_budget) or 0.0,
        budget_utilization=_round_rate(_safe_rate(spend_to_date, campaign.budget)),
        expected_spend_to_date=_round_currency(expected_spend_to_date) or 0.0,
        pacing_ratio=pacing_ratio,
        average_daily_spend=_round_currency(average_daily_spend) or 0.0,
        projected_total_spend=_round_currency(projected_total_spend) or 0.0,
        projected_budget_variance=_round_currency(projected_budget_variance) or 0.0,
        elapsed_days=elapsed_days,
        total_campaign_days=total_campaign_days,
        pacing_status=pacing_status,
    )


def aggregate_campaign(
    campaign: Campaign,
    metrics: Sequence[DailyMetric],
    start_date: date | None = None,
    end_date: date | None = None,
    as_of_date: date | None = None,
) -> CampaignReport:
    """Aggregate campaign metrics into a report model."""

    report_start_date, report_end_date = _resolve_report_window(campaign, start_date, end_date)
    all_metrics_frame = _build_metric_frame(metrics)

    if all_metrics_frame.empty:
        filtered_frame = all_metrics_frame.copy()
    else:
        filtered_frame = all_metrics_frame.loc[
            (all_metrics_frame["date"] >= pd.Timestamp(report_start_date))
            & (all_metrics_frame["date"] <= pd.Timestamp(report_end_date))
        ].copy()

    trend_frame = _build_trend_frame(filtered_frame, report_start_date, report_end_date)
    pacing = _build_pacing_insight(campaign, all_metrics_frame, as_of_date)

    if filtered_frame.empty:
        return CampaignReport(
            campaign_id=campaign.id,
            campaign_name=campaign.name,
            advertiser=campaign.advertiser,
            report_start_date=report_start_date,
            report_end_date=report_end_date,
            days_in_report=(report_end_date - report_start_date).days + 1,
            days_with_data=0,
            total_impressions=0,
            total_clicks=0,
            total_spend=0.0,
            total_conversions=0,
            ctr=0.0,
            cpa=None,
            best_performing_day=None,
            daily_breakdown=_serialize_daily_breakdown(trend_frame),
            pacing=pacing,
        )

    filtered_frame["ctr"] = filtered_frame.apply(lambda row: _safe_rate(row["clicks"], row["impressions"]), axis=1)
    filtered_frame["cpa"] = filtered_frame.apply(lambda row: _safe_cpa(row["spend"], row["conversions"]), axis=1)
    best_row = filtered_frame.sort_values(
        by=["conversions", "ctr", "spend", "date"],
        ascending=[False, False, True, True],
    ).iloc[0]

    total_impressions = int(filtered_frame["impressions"].sum())
    total_clicks = int(filtered_frame["clicks"].sum())
    total_spend = float(filtered_frame["spend"].sum())
    total_conversions = int(filtered_frame["conversions"].sum())

    best_performing_day = BestPerformingDay(
        date=best_row["date"].date(),
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
        report_start_date=report_start_date,
        report_end_date=report_end_date,
        days_in_report=(report_end_date - report_start_date).days + 1,
        days_with_data=len(filtered_frame.index),
        total_impressions=total_impressions,
        total_clicks=total_clicks,
        total_spend=_round_currency(total_spend) or 0.0,
        total_conversions=total_conversions,
        ctr=_round_rate(_safe_rate(total_clicks, total_impressions)),
        cpa=_round_currency(_safe_cpa(total_spend, total_conversions)),
        best_performing_day=best_performing_day,
        daily_breakdown=_serialize_daily_breakdown(trend_frame),
        pacing=pacing,
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
