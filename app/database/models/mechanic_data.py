# app/database/models/user_profile.py
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database.models.base import BaseModel
from sqlalchemy.dialects.postgresql import ARRAY
class MechanicData(BaseModel):
    __tablename__ = "mechanic_data"

    shop_name = Column(String, nullable=True)
    initial_charge = Column(String, nullable=True)
    year_of_experience = Column(String, nullable=True)
    service_area = Column(String, nullable=True)
    specialist = Column(ARRAY(String), nullable=True)
    national_id= Column(String, nullable=True)
    national_id_image_url= Column(String, nullable=True)
    certificate_image_url= Column(String, nullable=True)
    certificate_id= Column(String, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id",ondelete="CASCADE"), unique=True, nullable=False,)
    user = relationship("User", back_populates="mechanic_data")