from __future__ import annotations

import uuid
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Float, Integer, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import BaseModel
 # Enum for user roles
from app.database.models.enum import UserRole

if TYPE_CHECKING:
    from app.database.models.user import User



# ---------------- Ratings ---------------- #

class Ratings(BaseModel):
    __tablename__ = "rating_data"

    given_to: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    rating: Mapped[float] = mapped_column(Float, nullable=False)
    review: Mapped[Optional[str]] = mapped_column(String)

    given_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    rating_by: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="rating_by"),
        nullable=False,
    )

    # ---------------- Relationships ---------------- #

    user_given_to: Mapped["User"] = relationship(
        foreign_keys=[given_to],
        back_populates="ratings_received",
    )

    user_given_by: Mapped["User"] = relationship(
        foreign_keys=[given_by],
        back_populates="ratings_given",
    )


# ---------------- AverageRating ---------------- #

class AverageRating(BaseModel):
    __tablename__ = "average_rating"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    avg_rating: Mapped[float] = mapped_column(Float, nullable=False)
    total_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    user_type: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_type"),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="average_rating"
    )