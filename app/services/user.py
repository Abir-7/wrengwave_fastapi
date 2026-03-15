from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy import select 
from app.database.models.user import User
from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload
from app.schemas.user import UserWithProfileResponse
from app.database.models.user_car import UserCar
from app.database.models.user_location import UserLocation
from typing import List
from app.schemas.user import UserCarData
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
        return UserWithProfileResponse.model_validate(user.profile)
    
    async def save_user_car_data(self, user_id: str, car_data: List[UserCarData]) -> List[UserCar]:
        try:
            new_cars = [
                UserCar(**car, user_id=user_id)  # car is already a dict
                for car in car_data
                ]
            self.db.add_all(new_cars)
            await self.db.commit()
            for car in new_cars:
                await self.db.refresh(car)
            return new_cars
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to save car data: {str(e)}")
   
            


    async def update_user_location(self, user_id: str, latitude: float, longitude: float) -> "UserLocation":
        try:
            # Check if user location exists
            result = await self.db.execute(select(UserLocation).where(UserLocation.user_id == user_id))
            user_location = result.scalars().first()

            if user_location:
                # Update existing location
                user_location.latitude = latitude
                user_location.longitude = longitude
                await self.db.commit()
                await self.db.refresh(user_location)
            else:
                # Create new location
                user_location = UserLocation(user_id=user_id, latitude=latitude, longitude=longitude)
                self.db.add(user_location)
                await self.db.commit()
                await self.db.refresh(user_location)

            return user_location

        except Exception as e:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update user location: {str(e)}")