

import uuid

from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import BaseModel
from app.database.models.enum import BookingStatus , booking_status_enum



if TYPE_CHECKING:
    from app.database.models.user import User
    from app.database.models.customer_car_issue import UserCarIssue
    from app.database.models.service_price_details import ServicePriceDetails





# ---------------- Model ---------------- #

class CarBookingService(BaseModel):
    __tablename__ = "car_booking_services"

    # ---------------- Columns ---------------- #

    status: Mapped[BookingStatus] = mapped_column(
        booking_status_enum,
        nullable=False,
        default=BookingStatus.pending
    )

    user_car_issue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_car_issues.id", ondelete="CASCADE"),
        nullable=False,
    )

    mechanic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    booked_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ---------------- Relationships ---------------- #

    car_issue: Mapped["UserCarIssue"] = relationship(
        back_populates="service_booking"
    )

    mechanic: Mapped["User"] = relationship(
        foreign_keys=[mechanic_id],
        back_populates="mechanic_bookings"
    )

    customer: Mapped["User"] = relationship(
        foreign_keys=[booked_by],
        back_populates="customer_bookings"
    )

    service_price_details: Mapped["ServicePriceDetails"] = relationship(
        back_populates="car_booking_service",
        cascade="all, delete-orphan",uselist=False
    )