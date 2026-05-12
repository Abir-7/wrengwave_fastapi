from pydantic import BaseModel

from typing import Optional
from uuid import UUID
class UserLocationCreate(BaseModel):
    latitude: float
    longitude: float
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    user_id: str



class UserLocationResponse(UserLocationCreate):
    id: UUID
    user_id: UUID
    
    class Config:
        from_attributes = True


class GiveRatingCreate(BaseModel):
    given_to: UUID
    rating: float
    review: Optional[str]

class GetRatingReq(BaseModel):
    user_id: UUID
   


class BookingStatusReq(BaseModel):
    status: str

class CarDataCreate(BaseModel):
    brand: str
    model: str

class CarDataResponse(CarDataCreate):
    id: UUID

    class Config:
        from_attributes = True