from __future__ import annotations

import uuid
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import BaseModel

if TYPE_CHECKING:
    from app.database.models.user import User



class UserProfile(BaseModel):
    __tablename__ = "user_profiles"

    # ---------------- Columns ---------------- #

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    full_name: Mapped[Optional[str]] = mapped_column(String)
    bio: Mapped[Optional[str]] = mapped_column(String)
    avatar_url: Mapped[Optional[str]] = mapped_column(String)

    # ---------------- Relationships ---------------- #

    user: Mapped["User"] = relationship(
        back_populates="profile"
    )