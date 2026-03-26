from __future__ import annotations

import uuid
import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, DateTime, Enum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import BaseModel

if TYPE_CHECKING:
    from app.database.models.user import User


# ---------------- Enum ---------------- #

class AuthStatus(enum.Enum):
    pending = "pending"
    success = "success"
    expire = "expire"


# ---------------- Model ---------------- #

class UserAuthentication(BaseModel):
    __tablename__ = "user_authentications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    code: Mapped[Optional[str]] = mapped_column(String)
    token: Mapped[Optional[str]] = mapped_column(String)

    expire_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    status: Mapped[AuthStatus] = mapped_column(
        Enum(AuthStatus, name="auth_status"),
        nullable=False,
        server_default=AuthStatus.pending.value,
    )

    # ---------------- Relationship ---------------- #

    user: Mapped["User"] = relationship(
        back_populates="authentications"
    )


# ---------------- Index ---------------- #

Index(
    "idx_user_auth_user_created",
    UserAuthentication.user_id,
    UserAuthentication.created_at,
)