from app.database.models.base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String,Boolean    
from app.database.models.customer_car import UserCar
import uuid
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional
class UserCarImage(BaseModel):
    __tablename__ = "user_car_images"
    image_url: Mapped[str] = mapped_column(String)
    image_id: Mapped[str] = mapped_column(String)
    user_car: Mapped["UserCar"] = relationship(back_populates="car_image")
    is_linked: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=False,default=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )