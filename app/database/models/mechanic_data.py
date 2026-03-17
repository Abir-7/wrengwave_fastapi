# app/database/models/user_profile.py
from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database.models.base import BaseModel
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import JSONB
class MechanicData(BaseModel):
    __tablename__ = "mechanic_data"

    shop_name = Column(String, nullable=True)
    initial_charge = Column(String, nullable=True)
    year_of_experience = Column(Integer, nullable=True)
    service_area = Column(String, nullable=True)
    specialist = Column(ARRAY(String), nullable=True)
    national_image_id= Column(String, nullable=True)
    national_id_image_url= Column(String, nullable=True)
    certificates = Column(JSONB, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id",ondelete="CASCADE"), unique=True, nullable=False,)
    user = relationship("User", back_populates="mechanic_data")