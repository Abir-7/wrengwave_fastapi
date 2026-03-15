from pydantic import BaseModel

from typing import Optional
from uuid import UUID
class UserLocationCreate(BaseModel):
    latitude: float
    longitude: float
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None

class UserLocationResponse(UserLocationCreate):
    id: UUID
    user_id: UUID
    
    class Config:
        from_attributes = True

