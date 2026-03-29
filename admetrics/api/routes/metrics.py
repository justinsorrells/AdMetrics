"""Metric ingestion routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from admetrics.db.models import Campaign, DailyMetric
from admetrics.db.session import get_db
from admetrics.schemas.metric import DailyMetricCreate, DailyMetricRead

router = APIRouter(prefix="/campaigns", tags=["Metrics"])


@router.post("/{campaign_id}/metrics", response_model=DailyMetricRead, status_code=status.HTTP_201_CREATED)
def ingest_campaign_metric(
    campaign_id: int,
    payload: DailyMetricCreate,
    db: Session = Depends(get_db),
) -> DailyMetric:
    """Ingest a daily metric row for a campaign."""

    campaign = db.get(Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    if payload.date < campaign.start_date or payload.date > campaign.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Metric date must fall within the campaign date range",
        )

    existing_metric = db.scalar(
        select(DailyMetric).where(
            DailyMetric.campaign_id == campaign_id,
            DailyMetric.date == payload.date,
        )
    )
    if existing_metric is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A metric row for this campaign and date already exists",
        )

    metric = DailyMetric(campaign_id=campaign_id, **payload.model_dump())
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric
