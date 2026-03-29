"""Campaign CRUD routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from admetrics.db.models import Campaign
from admetrics.db.session import get_db
from admetrics.schemas.campaign import CampaignCreate, CampaignRead

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


@router.post("", response_model=CampaignRead, status_code=status.HTTP_201_CREATED)
def create_campaign(payload: CampaignCreate, db: Session = Depends(get_db)) -> Campaign:
    """Create a new campaign."""

    campaign = Campaign(**payload.model_dump())
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


@router.get("", response_model=list[CampaignRead])
def list_campaigns(db: Session = Depends(get_db)) -> list[Campaign]:
    """List all campaigns."""

    return list(db.scalars(select(Campaign).order_by(Campaign.id)).all())


@router.get("/{campaign_id}", response_model=CampaignRead)
def get_campaign(campaign_id: int, db: Session = Depends(get_db)) -> Campaign:
    """Fetch a single campaign by ID."""

    campaign = db.get(Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return campaign
