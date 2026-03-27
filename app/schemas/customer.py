from pydantic import BaseModel
from typing import Optional
class AIResponse(BaseModel):
    summary: str
    issue: Optional[str]
    severity_level: Optional[str]
    confidence_level: int



# ---------------USER CAR-----------------
class UserCarData(BaseModel):
    brand: str
    model:str
    year: str
    image_url:str
    image_id: str
    tag_number: str






class BookMechanic(BaseModel):
    mechanic_id: str
    car_issue_id: str