
from app.database.models.user_location import UserLocation
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
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