from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.mechanic import MechanicDataResponse,MechanicBaseData
from app.database.models.mechanic_data import MechanicData
from fastapi import HTTPException
from app.database.models.user_profile import UserProfile
from sqlalchemy import select
class MechanicService:
    def __init__(self, db:AsyncSession):
        self.db=db
    
    async def save_mechanic_data(self, mechanic_id: str, mechanic_data: MechanicBaseData,profile_image_url: str) -> MechanicDataResponse:
        try:
            new_mechanic = MechanicData(**mechanic_data.model_dump(),user_id=mechanic_id )  
            self.db.add(new_mechanic)
            await self.db.flush()
            get_user = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == mechanic_id)
)
            user = get_user.scalar_one_or_none()
        
            if user and profile_image_url:
                print(user.avatar_url)
                user.avatar_url = profile_image_url
             
            await self.db.commit()
            return MechanicDataResponse.model_validate(new_mechanic)
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to save mechanic data: {str(e)}")
        

       