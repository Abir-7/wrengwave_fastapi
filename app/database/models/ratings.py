from app.database.models.base import BaseModel
from sqlalchemy import Column, String, Float, ForeignKey,Integer
from sqlalchemy.dialects.postgresql import UUID
from app.database.models.user import UserRole
from sqlalchemy.dialects.postgresql import UUID, ENUM 
from sqlalchemy.orm import relationship
class Ratings(BaseModel):
    __tablename__ = "rating_data"
    given_to = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Float, nullable=False)  # e.g., 4.5
    review = Column(String, nullable=True)
    given_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating_by=Column(ENUM(UserRole, name="rating_by"), nullable=False)

class AverageRating(BaseModel):
    __tablename__ = "avarage_rating"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    avg_rating = Column(Float, nullable=False,)
    total_rating = Column(Integer, nullable=False)
    user_type=Column(ENUM(UserRole, name="user_type"), nullable=False)
    user=relationship("User", back_populates="average_rating")
    
    
