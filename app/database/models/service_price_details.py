from __future__ import annotations
import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from app.database.models.base import BaseModel
from typing import Dict
from app.database.models.service_booking import CarBookingService
from sqlalchemy.dialects.postgresql import JSONB

class ServicePriceDetails(BaseModel):
    __tablename__ = "service_price_details"
    booking_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("car_booking_services.id"),unique=True, nullable=False)
    total_price: Mapped[float]
    details: Mapped[Dict[str, float]] = mapped_column(JSONB)

    car_booking_service: Mapped["CarBookingService"] = relationship(back_populates="service_price_details")
