# app/database/models/user.py
from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from app.database.models.base import BaseModel
# from app.database.models.user_profile import UserProfile
# from app.database.models.user_authentication import  UserAuthentication
import enum

from sqlalchemy.dialects.postgresql import  ENUM 

class UserRole(enum.Enum):
    admin = "admin"
    customer = "customer"
    mechanic = "mechanic"



class User(BaseModel):
    __tablename__ = "users"

    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=False)
    role = Column(ENUM(UserRole, name="user_role"), nullable=False, server_default="customer")
    profile = relationship("UserProfile", back_populates="user", uselist=False,cascade="all, delete-orphan")

    average_rating = relationship(
        "AverageRating",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    authentications = relationship(
        "UserAuthentication",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    location = relationship("UserLocation", back_populates="user",uselist=False)
    cars = relationship("UserCar", back_populates="user")
    mechanic_data = relationship("MechanicData", back_populates="user",uselist=False)
    car_issues = relationship("UserCarIssue", back_populates="user")
    mechanic_info = relationship(
        "CarBookingService",
        foreign_keys="CarBookingService.mechanic_id",
        back_populates="mechanic"
    )

    customer_info = relationship(
        "CarBookingService",
        foreign_keys="CarBookingService.booked_by",
        back_populates="customer"
    )