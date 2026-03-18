from app.database.models.customer_car import UserCar
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from typing import List
from app.schemas.customer import UserCarData

class CustomerService:
    def __init__(self, db:AsyncSession):
        self.db=db
    
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