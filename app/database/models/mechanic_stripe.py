import uuid
from sqlalchemy import String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database.models.base import BaseModel

from typing import TYPE_CHECKING

if TYPE_CHECKING:
   from app.database.models.user import User

class MechanicStripe(BaseModel):
    __tablename__ = "mechanic_stripes"

    mechanic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # one stripe record per mechanic
    )

    stripe_account_id:      Mapped[str | None] = mapped_column(String, nullable=True)
    stripe_onboarded:       Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    stripe_charges_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    stripe_payouts_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_transfer_id:       Mapped[str | None] = mapped_column(String, nullable=True)
    last_transfer_amount:   Mapped[int | None] = mapped_column(Integer, nullable=True)

    # relationship back to user
    mechanic: Mapped["User"] = relationship("User", back_populates="stripe_info")