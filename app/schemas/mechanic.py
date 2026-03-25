from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
class Certificate(BaseModel):
    certificate_image_url: str
    certificate_image_id: str


class MechanicBaseData(BaseModel):
    shop_name: Optional[str]
    initial_charge: Optional[str]
    year_of_experience: Optional[int]
    service_area: Optional[str]
    specialist: Optional[List[str]]
    
    # File-related fields
    certificates: Optional[List[Certificate]] = []
    national_id_image_url: Optional[str] = None
    national_image_id: Optional[str] = None

class MechanicDataResponse(BaseModel):
    id: UUID
    shop_name: Optional[str]
    initial_charge: Optional[str]
    year_of_experience: Optional[int]
    service_area: Optional[str]
    specialist: Optional[List[str]]
    user_id: UUID
    # File-related fields
    certificates: Optional[List[Certificate]] = []
    national_id_image_url: Optional[str] = None
    national_image_id: Optional[str] = None
    
    model_config = {
        "from_attributes": True  
    }



class MechanicProfile(BaseModel):
    id: UUID
    shop_name: Optional[str]
    initial_charge: Optional[str]
    year_of_experience: Optional[int]
    service_area: Optional[str]
    specialist: Optional[List[str]]
    full_name: Optional[str]
    bio: Optional[str]
    avatar_url: Optional[str]
    avg_rating: Optional[float]
    total_rating: Optional[int]
    certificates: Optional[List[Certificate]] = []
    latitude: Optional[float]
    longitude: Optional[float]
    model_config = {
        "from_attributes": True  
    }
