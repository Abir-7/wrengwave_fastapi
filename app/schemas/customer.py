from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
class AIResponse(BaseModel):
    summary: str
    issue: Optional[str]
    severity_level: Optional[str]
    confidence_level: int



# ---------------USER CAR-----------------
class UserCarData(BaseModel):
    brand: str
    model:str
    year: int
    tag_number: str
    car_image_id: str
    license_plate: str

class UserCarDataResponse(BaseModel):
    id: UUID
    brand: str
    model: str
    year: int
    license_plate: str
    tag_number: str
    user_id: UUID
    image_url: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookMechanic(BaseModel):
    mechanic_id: str
    car_issue_id: str


class UpdateBookingStatus(BaseModel):
    status: str