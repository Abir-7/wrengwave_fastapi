
from app.database.models.user_location import UserLocation
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database.models.ratings import AverageRating,Ratings
from app.schemas.mechanic import MechanicProfile
from app.database.models.mechanic_data import MechanicData
from app.database.models.user_profile import UserProfile
from fastapi import HTTPException

class CommonService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def update_location(
            self, 
            user_id:str, 
            latitude: float, longitude: float,
            address: Optional[str] = None,
            city:Optional[str] = None,
            country:Optional[str] = None,
                              ):
        print(user_id, latitude, longitude)
        result = await self.db.execute(select(UserLocation).where(UserLocation.user_id == user_id))
        user_location = result.scalars().first()

        if user_location:
            user_location.latitude = latitude
            user_location.longitude = longitude
            if address is not None:
                user_location.address = address
            if city is not None:
                user_location.city = city
            if country is not None:
                user_location.country = country
         
        else:
            user_location = UserLocation(user_id=user_id, latitude=latitude, longitude=longitude, address=address, city=city, country=country)
            self.db.add(user_location)
            
        await self.db.commit()
        await self.db.refresh(user_location)

        return user_location
    
    async def give_rating(self, given_by, given_to, rating,review=None):
        new_rating=Ratings(given_by=given_by,given_to=given_to,rating=rating,review=review)
        self.db.add(new_rating)

        result = await self.db.execute(select(AverageRating).where(AverageRating.user_id == given_to))
        average_rating = result.scalars().first()

        if average_rating:
            average_rating.avg_rating = (
            average_rating.avg_rating * average_rating.total_rating + rating
        ) / (average_rating.total_rating + 1)
            average_rating.total_rating += 1
        else:
            raise ValueError("Average rating not found")

        await self.db.commit()
        await self.db.refresh(new_rating)
        return new_rating

    async def get_average_rating(self, user_id):
        result = await self.db.execute(select(AverageRating).where(AverageRating.user_id == user_id))
        average_rating = result.scalars().first()
        return average_rating
    

    async def get_mechanic_data(self, mechanic_id: str) -> MechanicProfile:
        profile=await self.db.execute(select(UserProfile).where(UserProfile.user_id == mechanic_id))
        profile=profile.scalar_one_or_none()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        result = await self.db.execute(select(MechanicData).where(MechanicData.user_id == mechanic_id))
        mechanic = result.scalar_one_or_none()

        if not mechanic:
            raise HTTPException(status_code=404, detail="Mechanic data not found")

        rating_data=await self.db.execute(select(AverageRating).where(AverageRating.user_id == mechanic_id))
        rating_data=rating_data.scalar_one_or_none()
        if not rating_data:
            raise HTTPException(status_code=404, detail="Rating data not found")
        
        location=await self.db.execute(select(UserLocation).where(UserLocation.user_id == mechanic_id))
        location=location.scalar_one_or_none()
        if not location:
            raise HTTPException(status_code=404, detail="Location not found")


        return  MechanicProfile(
            full_name=profile.full_name,
            avatar_url=profile.avatar_url,
            bio=profile.bio,
            id=mechanic.user_id,
            specialist=mechanic.specialist,
            certificates=mechanic.certificates,
            year_of_experience=mechanic.year_of_experience,
            initial_charge=mechanic.initial_charge,
            shop_name=mechanic.shop_name,
            avg_rating=rating_data.avg_rating,
            total_rating=rating_data.total_rating,
            latitude=location.latitude,
            longitude=location.longitude
        )

        