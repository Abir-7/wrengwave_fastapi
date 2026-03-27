from __future__ import annotations

import enum
from typing import List, Optional

from sqlalchemy import String, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import BaseModel

from app.database.models.user_profile import UserProfile
from app.database.models.customer_car import UserCar
from app.database.models.user_location import UserLocation
from app.database.models.mechanic_data import MechanicData
from app.database.models.service_booking import CarBookingService
from app.database.models.ratings import AverageRating
from app.database.models.user_authentication import UserAuthentication
from app.database.models.customer_car_issue import UserCarIssue
from app.database.models.enum import UserRole,user_role_enum
from app.database.models.ratings import Ratings



# -----------------------------
# User Model
# -----------------------------

class User(BaseModel):
    __tablename__ = "users"

    # ---------------- Columns ---------------- #

    email: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
        nullable=False,
    )

    hashed_password: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    role: Mapped[UserRole] = mapped_column(
      user_role_enum,
      nullable=False,
      default=UserRole.customer
    )

    # ---------------- Relationships ---------------- #

    # One-to-One
    profile: Mapped[Optional["UserProfile"]] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    location: Mapped[Optional["UserLocation"]] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    mechanic_data: Mapped[Optional["MechanicData"]] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    average_rating: Mapped[Optional["AverageRating"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False
    )

    # One-to-Many
    authentications: Mapped[List["UserAuthentication"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    cars: Mapped[List["UserCar"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    car_issues: Mapped[List["UserCarIssue"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # Bookings where this user is mechanic
    mechanic_bookings: Mapped[List["CarBookingService"]] = relationship(
        foreign_keys="CarBookingService.mechanic_id",
        back_populates="mechanic",
    )

    # Bookings where this user is customer
    customer_bookings: Mapped[List["CarBookingService"]] = relationship(
        foreign_keys="CarBookingService.booked_by",
        back_populates="customer",
    )

    # Ratings received by this user
    ratings_received: Mapped[List["Ratings"]] = relationship(
        foreign_keys="Ratings.given_to",
        back_populates="user_given_to",
        cascade="all, delete-orphan",
    )

    # Ratings given by this user
    ratings_given: Mapped[List["Ratings"]] = relationship(
        foreign_keys="Ratings.given_by",
        back_populates="user_given_by",
        cascade="all, delete-orphan",
    )