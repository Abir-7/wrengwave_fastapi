from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy import select
from app.database.models.user import User
from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload
from app.schemas.user import UserWithProfileResponse
class UserService:
    def __init__(self, db:AsyncSession):
        self.db=db
    
    async def get_user_profile(self, user_id: str) -> User:
        result = await self.db.execute(select(User).options(selectinload(User.profile)).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return UserWithProfileResponse.model_validate(user)