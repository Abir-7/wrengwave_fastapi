from __future__ import annotations

import uuid
from datetime import date, time
from typing import TYPE_CHECKING, Optional, List, Dict

from sqlalchemy import String, Float, Date, Time, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import BaseModel

if TYPE_CHECKING:
    from app.database.models.user import User
    from app.database.models.customer_car import UserCar
    from app.database.models.service_booking import CarBookingService


class UserCarIssue(BaseModel):
    __tablename__ = "user_car_issues"

    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)

    service_date: Mapped[Optional[date]] = mapped_column(Date)
    service_time: Mapped[Optional[time]] = mapped_column(Time)

    summary: Mapped[Optional[str]] = mapped_column(String)
    issue: Mapped[Optional[str]] = mapped_column(String)
    severity_level: Mapped[Optional[str]] = mapped_column(String)
    confidence_level: Mapped[Optional[Float]] = mapped_column(Float)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    user: Mapped["User"] = relationship(back_populates="car_issues")

    car_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_cars.id", ondelete="CASCADE"),
        nullable=False,
    )
    car: Mapped["UserCar"] = relationship(back_populates="car_issues")

    car_issue_data: Mapped[List["CarIssueData"]] = relationship(
        back_populates="user_car_issue",
        cascade="all, delete-orphan",
    )

    service_booking: Mapped[List["CarBookingService"]] = relationship(
        back_populates="car_issue",
        cascade="all, delete-orphan",
    )


class CarIssueData(BaseModel):
    __tablename__ = "car_issue_data"

    audio_files: Mapped[Optional[Dict]] = mapped_column(JSONB)
    image_files: Mapped[Optional[Dict]] = mapped_column(JSONB)
    description: Mapped[Optional[str]] = mapped_column(String)

    user_car_issue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_car_issues.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_car_issue: Mapped["UserCarIssue"] = relationship(
        back_populates="car_issue_data"
    )