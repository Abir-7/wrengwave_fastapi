from app.database.models.customer_car import UserCar
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, UploadFile
from typing import List
from app.schemas.customer import UserCarData
from app.core.http_client import get_client
from typing import Optional,List,Tuple
from app.utils.parse_time_date import parse_time_string, parse_date_string
from app.database.models.customer_car_issue import UserCarIssue
from app.database.models.user import User
from app.database.models.user_location import UserLocation
from sqlalchemy import select,func
from app.utils.distance_calculation import haversine
from app.database.models.user_profile import UserProfile
from app.database.models.mechanic_data import MechanicData
from app.database.models.service_booking import CarBookingService
from app.database.models.ratings import AverageRating


from app.database.models.enum import UserRole
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
        user_id:str,
        car_id: str,
        description: str,
        images: Optional[List[UploadFile]],
        audios: Optional[List[UploadFile]],
        service_date: str,
        service_time: str,
        latitude: Optional[float],
        longitude: Optional[float],
    ):
        if images and len(images) > 3:
            raise HTTPException(status_code=400, detail="Maximum 3 images allowed")

        files: list[tuple] = [
            ("description", (None, description)),
        ]

        tasks = []

        if images:
            tasks += [self._read_upload("images", img) for img in images]

        if audios:
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
            ai_data = response.json()

            new_issue = UserCarIssue(
            car_id=car_id,
            user_id=user_id,
            service_date=parse_date_string(service_date),
            service_time=parse_time_string(service_time),
            summary=ai_data.get("summary"),
            issue=ai_data.get("issue"),
            severity_level=ai_data.get("severity_level"),
            latitude=latitude,
            longitude=longitude
        )

            self.db.add(new_issue)
            await self.db.commit()
            return new_issue

        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="AI server timed out")

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=e.response.text,
            )
        
    async def get_mechanics(self, user_id: str, car_issue_id: str):
        user_id = str(user_id)
        car_issue_id = str(car_issue_id)

        # 1. Get car issue
        car_issue_result = await self.db.execute(
            select(UserCarIssue).where(
                UserCarIssue.user_id == user_id,
                UserCarIssue.id == car_issue_id
            )
        )
        car_issue = car_issue_result.scalar_one_or_none()

        if not car_issue:
            raise HTTPException(status_code=404, detail="Car issue not found")

        if car_issue.latitude is None or car_issue.longitude is None:
            raise HTTPException(status_code=400, detail="Car issue has no location")

        latitude = car_issue.latitude
        longitude = car_issue.longitude

        # 2. Fetch mechanics (without ratings)
        result = await self.db.execute(
            select(
                UserLocation,
                User,
                UserProfile,
                MechanicData,
                AverageRating
            )
            .join(User, User.id == UserLocation.user_id)
            .outerjoin(UserProfile, User.id == UserProfile.user_id)
            .outerjoin(MechanicData, User.id == MechanicData.user_id)
            .outerjoin(AverageRating, AverageRating.user_id == User.id)
            .where(User.role == UserRole.mechanic)
        )

        rows: list[tuple[UserLocation, User, UserProfile, MechanicData,AverageRating]] = result.all()

        # 3. Distance filtering
        nearby_mechanics = []

        for loc, user, profile, mechanic_data,rating in rows:
            if loc.latitude is None or loc.longitude is None:
                continue

            distance = haversine(latitude, longitude, loc.latitude, loc.longitude)

            if distance <= 2000:
                nearby_mechanics.append({
                    "mechanic_id": str(user.id),
                    # location
                    "distance_km": round(distance, 2),
                    "latitude": loc.latitude,
                    "longitude": loc.longitude,
                    # profile
                    "full_name": profile.full_name if profile else None,
                    "avatar_url": profile.avatar_url if profile else None,
                    # mechanic data
                    "shop_name": mechanic_data.shop_name if mechanic_data else None,
                    "initial_charge": mechanic_data.initial_charge if mechanic_data else None,
                    # rating
                    "avg_rating": rating.avg_rating if rating else None,
                    "total_rating": rating.total_rating if rating else None,
                
                })

        nearby_mechanics.sort(key=lambda x: x["distance_km"])
        return nearby_mechanics
    async def _read_upload(self, field: str, upload: UploadFile):
        data = await upload.read()
        return (field, (upload.filename, data, upload.content_type))