from app.database.models.base import BaseModel
from sqlalchemy import Column, String, ForeignKey,Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID


class UserCar(BaseModel):
    __tablename__ = "user_cars"
    brand = Column(String, nullable=False)       
    model = Column(String, nullable=False)      
    year = Column(Integer, nullable=False)
    license_plate = Column(String, unique=True)
    tag_number = Column(String)
    image_url = Column(String)
    image_id = Column(String)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id",ondelete="CASCADE"), nullable=False,)
    user = relationship("User", back_populates="cars")