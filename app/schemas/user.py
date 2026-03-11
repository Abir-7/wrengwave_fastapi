from pydantic import BaseModel, EmailStr
from uuid import UUID
from app.database.models.user import UserRole

# Profile model
class UserProfileResponse(BaseModel):
    full_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None

    model_config = {
        "from_attributes": True  # <-- Pydantic v2 replacement for orm_mode
    }

# Combined User model with non-optional profile
class UserWithProfileResponse(BaseModel):
    id: UUID
    email: EmailStr
    role: str  # or UserRole if you want strict typing
    is_active: bool
    profile: UserProfileResponse  # <-- now required

    model_config = {
        "from_attributes": True  # <-- enables nested ORM conversion
    }