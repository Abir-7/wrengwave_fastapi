from app.database.models.base import BaseModel
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

class CarBookingService(BaseModel):
    __tablename__ = "car_booking_services"

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