from sqlalchemy import Column, String, ForeignKey, DateTime, Enum ,Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.models.base import BaseModel
import enum

class AuthStatus(enum.Enum):
    pending = "pending"
    success = "success"
    expire = "expire"

class UserAuthentication(BaseModel):
    __tablename__ = "user_authentications"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id",ondelete="CASCADE"), nullable=False,)
    code = Column(String, nullable=True)  # optional
    token = Column(String, nullable=True)  # optional
    expire_time = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(AuthStatus, name="auth_status"), nullable=False, server_default="pending")

    # Relationship
    user = relationship("User", back_populates="authentications")
    
Index("idx_user_auth_user_created", UserAuthentication.user_id, UserAuthentication.created_at)