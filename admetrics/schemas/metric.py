"""Metric request and response schemas."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DailyMetricBase(BaseModel):
    """Shared daily metric fields."""

    date: date
    impressions: int = Field(ge=0)
    clicks: int = Field(ge=0)
    spend: float = Field(ge=0)
    conversions: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_funnel(self) -> "DailyMetricBase":
        """Catch impossible performance relationships."""

        if self.clicks > self.impressions:
            raise ValueError("clicks cannot exceed impressions")
        if self.conversions > self.clicks:
            raise ValueError("conversions cannot exceed clicks")
        return self


class DailyMetricCreate(DailyMetricBase):
    """Payload for ingesting a daily metric row."""


class DailyMetricRead(DailyMetricBase):
    """Metric response model."""

    id: int
    campaign_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
