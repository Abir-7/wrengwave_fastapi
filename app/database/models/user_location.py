from __future__ import annotations

import uuid
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import BaseModel

if TYPE_CHECKING:
    from app.database.models.user import User


class UserLocation(BaseModel):
    __tablename__ = "user_locations"

    # ---------------- Columns ---------------- #

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)

    address: Mapped[Optional[str]] = mapped_column(String)
    city: Mapped[Optional[str]] = mapped_column(String)
    country: Mapped[Optional[str]] = mapped_column(String)

    # ---------------- Relationship ---------------- #

    user: Mapped["User"] = relationship(
        back_populates="location"
    )