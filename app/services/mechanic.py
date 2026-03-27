from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.mechanic import MechanicDataResponse,MechanicBaseData
from app.database.models.mechanic_data import MechanicData
from fastapi import HTTPException
from app.database.models.user_profile import UserProfile
from app.database.models.user import User
from app.database.models.service_booking import CarBookingService,BookingStatus
from app.database.models.customer_car_issue import UserCarIssue
from sqlalchemy import select
from sqlalchemy.orm import joinedload
class MechanicService:
    def __init__(self, db:AsyncSession):
        self.db=db
    
    async def save_mechanic_data(self, mechanic_id: str, mechanic_data: MechanicBaseData,profile_image_url: str) -> MechanicDataResponse:
        try:
            new_mechanic = MechanicData(**mechanic_data.model_dump(),user_id=mechanic_id )  
            self.db.add(new_mechanic)
            await self.db.flush()
            get_user = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == mechanic_id))
            user = get_user.scalar_one_or_none()
            if user and profile_image_url:
                print(user.avatar_url)
                user.avatar_url = profile_image_url
            await self.db.commit()
            return MechanicDataResponse.model_validate(new_mechanic)
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to save mechanic data: {str(e)}")
        

    async def get_mechanics_all_booking_services(
        self, mechanic_id: str, booking_status: BookingStatus
    ) -> list[CarBookingService]:
            result=await self.db.execute(select(CarBookingService).where(  CarBookingService.mechanic_id == mechanic_id,
            CarBookingService.status == booking_status)
            .options(
                 joinedload(CarBookingService.customer).joinedload(User.profile),
                  joinedload(CarBookingService.car_issue)
                .joinedload(UserCarIssue.car)
            )
            )
            
            bookings = result.scalars().all()
            response = []
            for booking in bookings:
                user = booking.customer
                profile = user.profile if user else None
                issue = booking.car_issue
                car = issue.car if issue else None

                response.append({
                    "booking_id": str(booking.id),
                    "status": booking.status.value,

                    # user data
                    "customer_id": str(user.id) if user else None,
                    "customer_email": user.email if user else None,
                    "customer_name": profile.full_name if profile else None,
                    "customer_avatar": profile.avatar_url if profile else None,

                    # car data
                    "car_brand": car.brand if car else None,
                    "car_model": car.model if car else None,

                    # issue data
                    "issue_summary": issue.summary if issue else None,
                    "issue_detail": issue.issue if issue else None,
                    "severity_level": issue.severity_level if issue else None,
                    "service_date": issue.service_date if issue else None,
                    "service_time": issue.service_time if issue else None,
                })

            return response

    async def booking_detais(
        self, booking_id: str
    ) :
        result=await self.db.execute(select(CarBookingService).where(CarBookingService.id == booking_id).options(
            joinedload(CarBookingService.customer).joinedload(User.profile),
      joinedload(CarBookingService.customer)
        .joinedload(User.average_rating), joinedload(CarBookingService.customer)
        .joinedload(User.location),
            joinedload(CarBookingService.car_issue)
            .joinedload(UserCarIssue.car),
     
        ))
        booking = result.scalar_one_or_none()
        response = {
        "booking_id": str(booking.id),
        "status": booking.status.value if booking.status else None,
        "mechanic_id": str(booking.mechanic_id),
        "customer": {
            "user_id": str(booking.customer.id),
            "full_name": booking.customer.profile.full_name if booking.customer.profile else None,
            "email": booking.customer.email,
            "avatar_url": booking.customer.profile.avatar_url if booking.customer.profile else None,"avg_rating": booking.customer.average_rating.avg_rating if booking.customer.average_rating else None,
            "location":booking.customer.location.address if booking.customer.location else None,
            # "longitude": booking.customer.location.longitude if booking.customer.location else None,
            # "latitude": booking.customer.location.latitude if booking.customer.location else None
        },
        "car": {
            "brand": booking.car_issue.car.brand,
            "model": booking.car_issue.car.model,
            # "year": booking.car_issue.car.year,
            # "image_url": booking.car_issue.car.image_url
        },
        "issue": booking.car_issue.issue,
        "summary": booking.car_issue.summary,
        "service_date": booking.car_issue.service_date.isoformat() if booking.car_issue.service_date else None,
        "service_time": str(booking.car_issue.service_time) if booking.car_issue.service_time else None,
        "latitude": booking.car_issue.latitude,
        "longitude": booking.car_issue.longitude,
        "confidence_level": getattr(booking.car_issue, "confidence_level", None),
    }
        return response