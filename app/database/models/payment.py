from app.database.models.base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, String, Nullable
import uuid
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


    amount_refunded: Mapped[int] = mapped_column(default=0, nullable=False)
    refund_reason: Mapped[str | None] = mapped_column(String, nullable=True)


    failure_message: Mapped[str | None] = mapped_column(String, nullable=True)
    failure_code: Mapped[str | None] = mapped_column(String, nullable=True)


    transfer_id: Mapped[str | None] = mapped_column(String, nullable=True)

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