
from app.database.models.base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database.models.enum import PaymentStatus, payment_status_enum
class Payment(BaseModel):
    __tablename__ = "payments"
    payment_intent_id: Mapped[str]
    amount: Mapped[int]
    platform_fee: Mapped[int]

    currency: Mapped[str]
    status: Mapped[PaymentStatus] = mapped_column(
    payment_status_enum,
    default=PaymentStatus.UNPAID,
    nullable=False,
)

    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("car_booking_services.id", ondelete="CASCADE"),
        nullable=False,
    )

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    mechanic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )