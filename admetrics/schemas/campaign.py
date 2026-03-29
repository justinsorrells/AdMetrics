"""Campaign request and response schemas."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CampaignBase(BaseModel):
    """Shared campaign fields."""

    name: str = Field(min_length=1, max_length=255)
    advertiser: str = Field(min_length=1, max_length=255)
    budget: float = Field(gt=0)
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_dates(self) -> "CampaignBase":
        """Ensure campaign dates are ordered correctly."""

        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class CampaignCreate(CampaignBase):
    """Payload for creating a campaign."""


class CampaignRead(CampaignBase):
    """Campaign response model."""

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
