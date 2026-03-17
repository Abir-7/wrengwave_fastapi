# app/database/models/user_profile.py
from sqlalchemy import Column, String, ForeignKey, DateTime

from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database.models.base import BaseModel


class UserCarIssue(BaseModel):
    __tablename__ = "user_car_issues"
    audio_text= Column(String, nullable=True)
    description= Column(String, nullable=True)
    image_analysis_text= Column(String, nullable=True)
    service_date = Column(DateTime, nullable=False)
    

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id",ondelete="CASCADE"), nullable=False,)
    user = relationship("User", back_populates="car_issues")

    car_id=Column(UUID(as_uuid=True), ForeignKey("user_cars.id",ondelete="CASCADE"),  nullable=False,)
    car = relationship("UserCar", back_populates="car_issues")