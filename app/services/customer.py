from app.database.models.customer_car import UserCar
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, UploadFile
from typing import List
from app.schemas.customer import UserCarData, AIResponse
from app.core.http_client import get_client
from typing import Optional,List,Tuple
from app.utils.parse_time_date import parse_time_string, parse_date_string
from app.database.models.customer_car_issue import UserCarIssue
from app.database.models.user import User
from app.database.models.user_location import UserLocation
from sqlalchemy import select,update,delete
from sqlalchemy.orm import joinedload
from app.utils.distance_calculation import haversine
from app.database.models.user_profile import UserProfile
from app.database.models.mechanic_data import MechanicData
from app.database.models.service_booking import CarBookingService
from app.database.models.ratings import AverageRating
from app.database.models.enum import BookingStatus
from app.database.models.customer_car_image import UserCarImage
from app.database.models.enum import UserRole
from app.schemas.customer import UserCarDataResponse

from app.utils.join_image_url import ensure_full_url

import httpx
import asyncio



AI_SERVER_URL = "http://localhost:5000"

class CustomerService:
    def __init__(self, db:AsyncSession):
        self.db=db
    #-------------------------
    async def save_user_car_image(self, user_id: str,  image_url:str):
        try:
            new_car_image = UserCarImage(user_id=user_id, image_url=image_url,image_id=image_url,is_linked=False)
            self.db.add(new_car_image)
            await self.db.commit()
            await self.db.refresh(new_car_image)
            return {"image_data_id":new_car_image.id}
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to save car image: {str(e)}")
     # ------------------------
    async def save_user_car_data(self, user_id: str, car_data: List[UserCarData]) -> List[UserCar]:
        try:
            new_cars = [
                UserCar(**car.model_dump(), user_id=user_id)  # car is already a dict
                for car in car_data
                ]
            self.db.add_all(new_cars)
    
            await self.db.flush()
            for car in new_cars:
                await self.db.execute(update(UserCarImage).where(UserCarImage.id == car.car_image_id).values(is_linked=True))
                await self.db.refresh(car)
            
            await self.db.commit()
            return new_cars
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to save car data: {str(e)}")
    # -----------------------
    async def get_users_cars(self, user_id: str)-> List[UserCarDataResponse]:
        result = await self.db.execute(select(UserCar).where(UserCar.user_id == user_id).options(joinedload(UserCar.car_image)))
        cars = result.scalars().all()

        response = []
        for car in cars:
            response.append(
                UserCarDataResponse(
                **{k: getattr(car, k) for k in ['id','brand','model','year','license_plate','tag_number','user_id','created_at','updated_at']},
                image_url=  ensure_full_url(getattr(car.car_image, 'image_url', None))  # flatten image id
            )
        )

        return response
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
            ai_data_obj = AIResponse(**ai_data)

            new_issue = UserCarIssue(
            car_id=car_id,
            user_id=user_id,
            service_date=parse_date_string(service_date),
            service_time=parse_time_string(service_time),
            summary=ai_data_obj.summary,
            issue=ai_data_obj.issue,
            severity_level=ai_data_obj.severity_level,
            confidence_level=ai_data_obj.confidence_level,
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
    #------------------------
    async def get_users_car_issues(
        self,
        user_id: str,
        car_id: Optional[str] = None
    ) -> List[dict]:

        # 🔹 Base query
        query = (
            select(UserCarIssue)
            .options(
                joinedload(UserCarIssue.service_booking),
                joinedload(UserCarIssue.car).joinedload(UserCar.car_image)
            )
            .where(UserCarIssue.user_id == user_id)
        )

        # 🔹 Optional filter
        if car_id:
            query = query.where(UserCarIssue.car_id == car_id)

        # 🔹 Execute query
        result = await self.db.execute(query)
        issues = result.unique().scalars().all()

        # 🔹 Format response
        formatted_issues = []

        for issue in issues:
            car = issue.car
            car_image = car.car_image if car else None
            booking = issue.service_booking

            formatted_issues.append({
                "id": issue.id,
                "issue": issue.issue,
                "summary": issue.summary,
                "service_date": issue.service_date,
                "service_time": issue.service_time,
                "status": booking.status if booking else None,

                "car": {
                    "brand": car.brand,
                    "model": car.model,
                    "image_url": ensure_full_url(car_image.image_url) if car_image else None
                } if car else None,
            })

        return formatted_issues
    # ------------------------
    async def users_car_issue_details(
        self,
        car_issue_id: str,
        user_id: str
    ) -> List[dict]:

        # 🔹 Base query
        query = (
            select(UserCarIssue)
            .options(
                joinedload(UserCarIssue.service_booking),
                joinedload(UserCarIssue.car).joinedload(UserCar.car_image)
            )
            .where(UserCarIssue.id == car_issue_id, UserCarIssue.user_id == user_id)
        )

        # 🔹 Execute query
        result = await self.db.execute(query)
        issue = result.scalar_one_or_none()

        car = issue.car
        car_image = car.car_image if car else None
        booking = issue.service_booking

        return{
                "id": issue.id,
                "issue": issue.issue,
                "summary": issue.summary,
                "service_date": issue.service_date,
                "service_time": issue.service_time,
                "status": booking.status if booking else None,

                "car": {
                    "brand": car.brand,
                    "model": car.model,
                    "image_url": ensure_full_url(car_image.image_url) if car_image else None
                } if car else None,
            }

    # ------------------------
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
            print(distance)
            if distance <= 4000:
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
    # --------------------------
    async def book_mechanic(self, mechanic_id: str,car_issue_id: str,user_id: str):
        try:
            mechanic_id = str(mechanic_id)
            car_issue_id = str(car_issue_id)
            user_id = str(user_id)

            get_existing_booking = await self.db.execute(select(CarBookingService).where(CarBookingService.user_car_issue_id == car_issue_id))
            existing_booking = get_existing_booking.scalar_one_or_none()

            if(existing_booking and existing_booking.status == "rejected"): 
                # delete existing booking
                await self.db.execute(delete(CarBookingService).where(CarBookingService.user_car_issue_id == car_issue_id))
                await self.db.flush()
                existing_booking = None
            
            
            if existing_booking:
                raise HTTPException(status_code=400, detail="Car issue has already been booked")

            new_booking = CarBookingService(
                booked_by=user_id,
                mechanic_id=mechanic_id,
                user_car_issue_id=car_issue_id,
            )

            self.db.add(new_booking)
            await self.db.commit()
            await self.db.refresh(new_booking)
            return new_booking
        except Exception as e:
            await self.db.rollback()
            raise e
    #-------HELPER----------- 
    async def _read_upload(self, field: str, upload: UploadFile):
        data = await upload.read()
        return (field, (upload.filename, data, upload.content_type))