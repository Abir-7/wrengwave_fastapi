from app.database.models.customer_car import UserCar
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, UploadFile
from typing import List
from app.schemas.customer import UserCarData
from app.core.http_client import get_client
from typing import Optional
import httpx
import asyncio
AI_SERVER_URL = "http://localhost:5000"

class CustomerService:
    def __init__(self, db:AsyncSession):
        self.db=db
    
     # ------------------------
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
        

    # ------------------------
    async def analyze_car_issue(
        self,
        car_id: str,
        description: str,
        images: Optional[List[UploadFile]],
        audios: Optional[List[UploadFile]],
        service_date: str,
    ):
        if images and len(images) > 3:
            raise HTTPException(status_code=400, detail="Maximum 3 images allowed")

        files: list[tuple] = [
            ("description", (None, description)),
        ]

        tasks = []

        if images:
            tasks += [self._read_upload("images", img) for img in images]

        if audio:
            tasks += [self._read_upload("audios", aud) for aud in audios]

        results = await asyncio.gather(*tasks)
        files.extend(results)

        try:
            client = get_client()

            response = await client.post(
                f"{AI_SERVER_URL}/analysis/car",
                files=files,
            )

            response.raise_for_status()
            car_issue = response.json()

            service_date 
            car_id

            return car_issue

        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="AI server timed out")

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=e.response.text,
            )
        












         # -----------HELPER-------------
    
    async def _read_upload(self, field: str, upload: UploadFile):
        data = await upload.read()
        return (field, (upload.filename, data, upload.content_type))