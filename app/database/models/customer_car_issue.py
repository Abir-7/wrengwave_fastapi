# app/database/models/user_profile.py
from sqlalchemy import Column, String, ForeignKey, Date, Time,Float

from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database.models.base import BaseModel
from sqlalchemy.dialects.postgresql import JSONB

class UserCarIssue(BaseModel):
    __tablename__ = "user_car_issues"

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    service_date = Column(Date, nullable=True)
    service_time = Column(Time, nullable=True)
    summary = Column(String, nullable=True)
    issue = Column(String, nullable=True)
    severity_level = Column(String, nullable=True)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id",ondelete="CASCADE"), nullable=False,)
    user = relationship("User", back_populates="car_issues")

    car_id=Column(UUID(as_uuid=True), ForeignKey("user_cars.id",ondelete="CASCADE"),  nullable=False,)
    car = relationship("UserCar", back_populates="car_issues")

    car_issue_data = relationship("CarIssueData", back_populates="user_car_issue")
    
    service_booking = relationship("CarBookingService", back_populates="car_issue")


class CarIssueData(BaseModel):
    __tablename__ = "car_issue_data"
    
    audio_files = Column(JSONB, nullable=True)
    image_files = Column(JSONB, nullable=True)
    description= Column(String, nullable=True)

    user_car_issue_id=Column(UUID(as_uuid=True), ForeignKey("user_car_issues.id",ondelete="CASCADE"), nullable=False,)
    user_car_issue = relationship("UserCarIssue", back_populates="car_issue_data")

