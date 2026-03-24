from app.database.models.base import BaseModel
from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
class MechanicRating(BaseModel):
    __tablename__ = "mechanic_ratings"

    mechanic_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Float, nullable=False)  # e.g., 4.5
    review = Column(String, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)