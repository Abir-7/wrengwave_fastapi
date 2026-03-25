from app.database.models.base import BaseModel
from sqlalchemy import Column, ForeignKey,Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

import enum

class BookingStatus(enum.Enum):
    pending = "pending"
    arrived = "arrived"
    inspecting = "inspecting"
    canceled = "canceled"
    repairing = "repairing"
    completed = "completed"
    paid = "paid"

class CarBookingService(BaseModel):
    __tablename__ = "car_booking_services"

    status = Column(
        Enum(BookingStatus, name="booking_status",),
        nullable=False,
        server_default="pending",
        
    )


    user_car_issue_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_car_issues.id", ondelete="CASCADE"),
        nullable=False,
    )

    mechanic_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    booked_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    car_issue = relationship(
        "UserCarIssue",
        back_populates="service_booking"
    )


    mechanic = relationship(
        "User",
        foreign_keys=[mechanic_id],
        back_populates="mechanic_info"
    )

    customer = relationship(
        "User",
        foreign_keys=[booked_by],
        back_populates="customer_info"
    )