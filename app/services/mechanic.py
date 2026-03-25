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

                    # car data
                    "car_brand": car.brand if car else None,
                    "car_model": car.model if car else None,

                    # issue data
                    "issue_summary": issue.summary if issue else None,
                    "issue_detail": issue.issue if issue else None,
                    "service_date": issue.service_date if issue else None,
                    "service_time": issue.service_time if issue else None,
                })

            return response
#     async def get_mechanics_all_booking_services(
#     self, mechanic_id: str, booking_status: BookingStatus
# ) :
#         result = await self.db.execute(
#             select(
#                 CarBookingService.id,
#                 CarBookingService.status,
#                 User.id.label("customer_id"),
#                 User.email.label("customer_email"),
#                 UserProfile.full_name.label("customer_name"),
#                 Car.brand.label("car_brand"),
#                 Car.model.label("car_model"),
#                 UserCarIssue.summary.label("issue_summary"),
#                 UserCarIssue.issue.label("issue_detail"),
#                 UserCarIssue.service_date,
#                 UserCarIssue.service_time,
#             )
#             .join(User, CarBookingService.customer_id == User.id, isouter=True)
#             .join(UserProfile, User.id == UserProfile.user_id, isouter=True)
#             .join(UserCarIssue, CarBookingService.car_issue_id == UserCarIssue.id, isouter=True)
#             .join(Car, UserCarIssue.car_id == Car.id, isouter=True)
#             .where(
#                 CarBookingService.mechanic_id == mechanic_id,
#                 CarBookingService.status == booking_status,
#             )
#         )

#         rows = result.mappings().all()
#         return [
#             BookingServiceResponse(
#                 booking_id=str(row.id),
#                 status=row.status.value,
#                 customer_id=str(row.customer_id) if row.customer_id else None,
#                 customer_email=row.customer_email,
#                 customer_name=row.customer_name,
#                 car_brand=row.car_brand,
#                 car_model=row.car_model,
#                 issue_summary=row.issue_summary,
#                 issue_detail=row.issue_detail,
#                 service_date=row.service_date,
#                 service_time=row.service_time,
#             )
#             for row in rows
#         ]