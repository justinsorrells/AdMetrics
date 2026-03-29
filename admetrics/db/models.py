"""Database models."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from admetrics.db.session import Base


class Campaign(Base):
    """Advertising campaign metadata."""

    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    advertiser: Mapped[str] = mapped_column(String(255), nullable=False)
    budget: Mapped[float] = mapped_column(Float, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    metrics: Mapped[list["DailyMetric"]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
        order_by="DailyMetric.date",
    )


class DailyMetric(Base):
    """Daily performance metrics for a campaign."""

    __tablename__ = "daily_metrics"
    __table_args__ = (UniqueConstraint("campaign_id", "date", name="uq_campaign_metric_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    impressions: Mapped[int] = mapped_column(Integer, nullable=False)
    clicks: Mapped[int] = mapped_column(Integer, nullable=False)
    spend: Mapped[float] = mapped_column(Float, nullable=False)
    conversions: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    campaign: Mapped[Campaign] = relationship(back_populates="metrics")
