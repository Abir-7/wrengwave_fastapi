
from app.database.models.user_location import UserLocation
from sqlalchemy import select,update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database.models.ratings import AverageRating,Ratings
from app.schemas.mechanic import MechanicProfile
from app.database.models.mechanic_data import MechanicData
from app.database.models.user_profile import UserProfile
from fastapi import HTTPException
from app.database.models.service_booking import CarBookingService,BookingStatus
from sqlalchemy.orm import joinedload
from app.database.models.user import User
from app.database.models.enum import UserRole
from app.utils.join_image_url import ensure_full_url
from app.database.models.customer_car_issue import UserCarIssue
from sqlalchemy.engine import CursorResult
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
        print(mechanic_id)
        profile=await self.db.execute(select(UserProfile).where(UserProfile.user_id == mechanic_id))
        profile=profile.scalar_one_or_none()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        result = await self.db.execute(select(MechanicData).where(MechanicData.user_id == mechanic_id).options(joinedload(MechanicData.user).joinedload(User.mechanic_image_data)))
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
            avatar_url=ensure_full_url(profile.avatar_url) if profile.avatar_url else None,
            bio=profile.bio,
            id=mechanic.user_id,
            specialist=mechanic.specialist,
            certificates=[
    {
        **cert,
        "certificate_image_url": ensure_full_url(cert["certificate_image_url"]),
       
    }
    for cert in (mechanic.user.mechanic_image_data.certificates or [])
],
            year_of_experience=mechanic.year_of_experience,
            initial_charge=mechanic.initial_charge,
            shop_name=mechanic.shop_name,
            avg_rating=rating_data.avg_rating,
            total_rating=rating_data.total_rating,
            latitude=location.latitude,
            longitude=location.longitude
          
        )

    async def get_bookings_progress(self, booking_id: str,user_role:str):

        if user_role == "customer":
            result = await self.db.execute(
                select(CarBookingService).options(joinedload(CarBookingService.mechanic).joinedload(User.profile),
                joinedload(CarBookingService.mechanic).joinedload(User.average_rating),joinedload(CarBookingService.service_price_details))
                .where(CarBookingService.id == booking_id)
            )
            booking = result.scalar_one_or_none()
            if not booking:
                raise HTTPException(status_code=404, detail="Booking not found")
            return {
                "id": str(booking.id),
                "status": booking.status,
                "service_price_details": {
                    "total_price": booking.service_price_details.total_price if booking.service_price_details else None,
                    "details": booking.service_price_details.details if booking.service_price_details else None,
                },
                "user": {
                    "id": str(booking.mechanic.id),
                    "full_name": booking.mechanic.profile.full_name,
                    "avatar_url": booking.mechanic.profile.avatar_url,
                    "avg_rating": booking.mechanic.average_rating.avg_rating,
                }
            }

        if user_role == "mechanic":
            result = await self.db.execute(
                select(CarBookingService).options(joinedload(CarBookingService.customer).joinedload(User.profile),
                joinedload(CarBookingService.customer).joinedload(User.average_rating),joinedload(CarBookingService.service_price_details))
                .where(CarBookingService.id == booking_id)
            )
            booking = result.scalar_one_or_none()
            if not booking:
                raise HTTPException(status_code=404, detail="Booking not found")
            return {
                "id": str(booking.id),
                "status": booking.status,
                "service_price_details": {
                    "total_price": booking.service_price_details.total_price if booking.service_price_details else None,
                    "details": booking.service_price_details.details if booking.service_price_details else None,
                },
                "user": {
                    "id": str(booking.customer.id),
                    "full_name": booking.customer.profile.full_name,
                    "avatar_url": booking.customer.profile.avatar_url,
                    "avg_rating": booking.customer.average_rating.avg_rating,
                }
            }

        raise HTTPException(status_code=400, detail="Invalid user role")
    

    async def change_booking_status(self, booking_id: str, booking_status: BookingStatus, user_id: str, user_role: str) -> None:
        try:
            if user_role == UserRole.mechanic.value:
                result:CursorResult = await self.db.execute(
                    update(CarBookingService)
                    .where(CarBookingService.id == booking_id, CarBookingService.mechanic_id == user_id)
                    .values(status=booking_status)
                )

            elif user_role == UserRole.customer.value:
                result:CursorResult= await self.db.execute(
                    update(CarBookingService)
                    .where(CarBookingService.id == booking_id, CarBookingService.booked_by == user_id)
                    .values(status=booking_status)
                )

            else:
                raise HTTPException(status_code=403, detail="Unauthorized role to change booking status")

            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Booking data not found. ")

            await self.db.commit()
            return {
                "message": "Booking status updated successfully",
                "booking_id": booking_id,
                "status": booking_status,
            }

        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update booking status: {str(e)}")
    
    
    
    # async def get_all_bookings(self,user_role:UserRole, booking_status: Optional[BookingStatus] = None,user_id:Optional[str]=None):
  
    #     result = await self.db.execute(select(CarBookingService).options(joinedload(CarBookingService.mechanic).joinedload(User.profile),joinedload(CarBookingService.mechanic).joinedload(User.location),joinedload(CarBookingService.customer).joinedload(User.location),
    #     joinedload(CarBookingService.customer).joinedload(User.profile),joinedload(CarBookingService.service_price_details),joinedload(CarBookingService.car_issue).joinedload(UserCarIssue.car)).where(CarBookingService.status == booking_status).order_by(CarBookingService.created_at.desc()))

    #     bookings = result.scalars().unique().all()
 
    #     result =[]

    #     for booking in bookings:
    #         data= {   
    #     "id": booking.id,
    #     "status": booking.status,
    #     "created_at": booking.created_at,
    #     "updated_at": booking.updated_at,
        
    #     "car_issue": {
    #         "id": booking.car_issue.id,
    #         "summary": booking.car_issue.summary,
    #         "issue": booking.car_issue.issue,
    #         "service_date": booking.car_issue.service_date,
    #         "service_time": booking.car_issue.service_time,
    #         "latitude": booking.car_issue.latitude,
    #         "longitude": booking.car_issue.longitude,
    #         "model": booking.car_issue.car.model if booking.car_issue.car else None,
    #         "brand": booking.car_issue.car.brand if booking.car_issue.car else None,
    #     } if booking.car_issue else None,
    #         }
    #         if user_role=="mechanic":
    #             data["user"]={
    #         "id": booking.customer.id,
    #         "email": booking.customer.email,
    #         "full_name": booking.customer.profile.full_name if booking.customer.profile else None,
    #         "avatar_url": ensure_full_url(booking.customer.profile.avatar_url) if booking.customer.profile.avatar_url else None,
    #         "latitude": booking.customer.location.latitude if booking.customer.location else None,
    #         "longitude": booking.customer.location.longitude if booking.customer.location else None,
    #         } if booking.customer else None,
      

    #         if user_role=="customer":
    #             data["user"]={
    #         "id": booking.mechanic.id,
    #         "email": booking.mechanic.email,
    #         "full_name": booking.mechanic.profile.full_name if booking.mechanic.profile else None,
    #         "avatar_url": ensure_full_url(booking.mechanic.profile.avatar_url) if booking.mechanic.profile.avatar_url else None,
    #         "latitude": booking.mechanic.location.latitude if booking.mechanic.location else None,
    #         "longitude": booking.mechanic.location.longitude if booking.mechanic.location else None,
    #         }if booking.mechanic else None
    #         return result.append(data)
        

    #     return result
    
    async def get_all_bookings(
    self,
    user_role: UserRole,
    booking_status: Optional[BookingStatus] = None,
    user_id: Optional[str] = None
    ):
        # Base query
        query = select(CarBookingService).options(
            joinedload(CarBookingService.mechanic)
                .joinedload(User.profile),
            joinedload(CarBookingService.mechanic)
                .joinedload(User.location),
            joinedload(CarBookingService.customer)
                .joinedload(User.location),
            joinedload(CarBookingService.customer)
                .joinedload(User.profile),
            joinedload(CarBookingService.service_price_details),
            joinedload(CarBookingService.car_issue)
                .joinedload(UserCarIssue.car)
        )

        # Filter by booking status if provided
        if booking_status:
            query = query.where(CarBookingService.status == booking_status)

        # Filter by user role
        if user_role == "customer" and user_id:
            query = query.where(CarBookingService.customer_id == user_id)
        elif user_role == "mechanic" and user_id:
            query = query.where(CarBookingService.mechanic_id == user_id)

        query = query.order_by(CarBookingService.created_at.desc())

        result_set = await self.db.execute(query)
        bookings = result_set.scalars().unique().all()

        result = []

        for booking in bookings:
            data = {
                "id": booking.id,
                "status": booking.status,
                "created_at": booking.created_at,
                "updated_at": booking.updated_at,
                "car_issue": {
                    "id": booking.car_issue.id,
                    "summary": booking.car_issue.summary,
                    "issue": booking.car_issue.issue,
                    "service_date": booking.car_issue.service_date,
                    "service_time": booking.car_issue.service_time,
                    "latitude": booking.car_issue.latitude,
                    "longitude": booking.car_issue.longitude,
                    "model": booking.car_issue.car.model if booking.car_issue.car else None,
                    "brand": booking.car_issue.car.brand if booking.car_issue.car else None,
                } if booking.car_issue else None,
            }

            # Add user info based on role
            if user_role == "mechanic" and booking.customer:
                data["user"] = {
                    "id": booking.customer.id,
                    "email": booking.customer.email,
                    "full_name": booking.customer.profile.full_name if booking.customer.profile else None,
                    "avatar_url": ensure_full_url(booking.customer.profile.avatar_url) if booking.customer.profile and booking.customer.profile.avatar_url else None,
                    "latitude": booking.customer.location.latitude if booking.customer.location else None,
                    "longitude": booking.customer.location.longitude if booking.customer.location else None,
                }
            elif user_role == "customer" and booking.mechanic:
                data["user"] = {
                    "id": booking.mechanic.id,
                    "email": booking.mechanic.email,
                    "full_name": booking.mechanic.profile.full_name if booking.mechanic.profile else None,
                    "avatar_url": ensure_full_url(booking.mechanic.profile.avatar_url) if booking.mechanic.profile and booking.mechanic.profile.avatar_url else None,
                    "latitude": booking.mechanic.location.latitude if booking.mechanic.location else None,
                    "longitude": booking.mechanic.location.longitude if booking.mechanic.location else None,
                }

            result.append(data)

        return bookings