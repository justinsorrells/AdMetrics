"""Reporting routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

from admetrics.db.models import Campaign
from admetrics.db.session import get_db
from admetrics.schemas.report import CampaignComparison, CampaignReport
from admetrics.services.aggregator import aggregate_campaign, compare_campaigns

router = APIRouter(tags=["Reports"])


def _get_campaign_with_metrics(db: Session, campaign_id: int) -> Campaign:
    """Load a campaign and its metrics or raise a 404."""

    campaign = db.scalar(
        select(Campaign)
        .options(selectinload(Campaign.metrics))
        .where(Campaign.id == campaign_id)
    )
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return campaign


@router.get("/campaigns/{campaign_id}/report", response_model=CampaignReport)
def get_campaign_report(campaign_id: int, db: Session = Depends(get_db)) -> CampaignReport:
    """Return aggregated reporting metrics for a campaign."""

    campaign = _get_campaign_with_metrics(db, campaign_id)
    return aggregate_campaign(campaign, campaign.metrics)


@router.get("/reports/compare", response_model=CampaignComparison)
def compare_campaign_reports(
    a: int = Query(..., description="Campaign ID for the first campaign"),
    b: int = Query(..., description="Campaign ID for the second campaign"),
    db: Session = Depends(get_db),
) -> CampaignComparison:
    """Compare two campaigns side by side."""

    if a == b:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comparison requires two different campaign IDs",
        )

    campaign_a = _get_campaign_with_metrics(db, a)
    campaign_b = _get_campaign_with_metrics(db, b)
    report_a = aggregate_campaign(campaign_a, campaign_a.metrics)
    report_b = aggregate_campaign(campaign_b, campaign_b.metrics)
    return compare_campaigns(report_a, report_b)
