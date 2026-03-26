from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import BaseModel

if TYPE_CHECKING:
    from app.database.models.user import User
    from app.database.models.customer_car_issue import UserCarIssue


class UserCar(BaseModel):
    __tablename__ = "user_cars"

    brand: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    license_plate: Mapped[str] = mapped_column(String, unique=True)
    tag_number: Mapped[str] = mapped_column(String)
    image_url: Mapped[str] = mapped_column(String)
    image_id: Mapped[str] = mapped_column(String)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="cars"
    )

    car_issues: Mapped[List["UserCarIssue"]] = relationship(
        back_populates="car",
        cascade="all, delete-orphan"
    )