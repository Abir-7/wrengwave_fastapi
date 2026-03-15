from app.database.models.base import BaseModel
from sqlalchemy import Column, String, ForeignKey,Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

class UserLocation(BaseModel):
    __tablename__ = "user_locations"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id",ondelete="CASCADE"), unique=True, nullable=False,)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    country = Column(String, nullable=True)
    user = relationship("User", back_populates="location")