from __future__ import annotations

import uuid
from typing import Optional, TYPE_CHECKING, List

from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.models.base import BaseModel

if TYPE_CHECKING:
    from app.database.models.user import User
    from app.database.models.mechanic_image_data import MechanicImageData


class MechanicData(BaseModel):
    __tablename__ = "mechanic_data"

    shop_name: Mapped[Optional[str]] = mapped_column(String)
    initial_charge: Mapped[Optional[str]] = mapped_column(String)
    year_of_experience: Mapped[Optional[int]] = mapped_column(Integer)
    service_area: Mapped[Optional[str]] = mapped_column(String)

    specialist: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))


    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="mechanic_data"
    )

