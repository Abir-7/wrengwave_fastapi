from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.database.models.base import BaseModel

class CarData(BaseModel):
    __tablename__ = "car_data"

    brand: Mapped[str] = mapped_column(String, nullable=False, index=True)
    model: Mapped[str] = mapped_column(String, nullable=False, index=True)
