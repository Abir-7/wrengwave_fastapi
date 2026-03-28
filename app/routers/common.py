from fastapi import APIRouter, Depends, HTTPException, status

from app.database.dependencies import get_common_service
from app.services.common import CommonService
from app.dependencies.auth import require_role
from app.database.models.enum import UserRole
from app.schemas.auth import TokenPayload
from app.schemas.common import UserLocationCreate,UserLocationResponse,GiveRatingCreate, GetRatingReq
from app.services.common import CommonService
from app.schemas.user import UserWithProfileResponse
from app.database.dependencies import get_user_service
from app.dependencies.auth import get_current_user
from app.services.user import UserService
from app.schemas.common import BookingStatusReq
from app.database.models.service_booking import BookingStatus



router = APIRouter(prefix="/common", tags=["common"])

@router.get("/me",response_model=UserWithProfileResponse)
async def get_me(
    current_user: TokenPayload = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)):

    return await user_service.get_user_profile(current_user.user_id)


@router.post("/locations", response_model=UserLocationResponse)
async def update_user_location(
    payload:UserLocationCreate,
    credentials: TokenPayload = Depends(require_role(UserRole.mechanic,UserRole.customer)),
    common_service: CommonService = Depends(get_common_service)):
    return await common_service.update_location(credentials.user_id, payload.latitude, payload.longitude , payload.address, payload.city, payload.country)

@router.get("/add-rating")
async def add_rating(
    payload: GiveRatingCreate,
    common_service: CommonService = Depends(get_common_service),
    credentials: TokenPayload = Depends(require_role(UserRole.mechanic,UserRole.customer))):
    return await common_service.give_rating(given_by=credentials.user_id,given_to=payload.given_to,rating=payload.rating,review=payload.review)

@router.get("/average-rating")
async def get_average_rating(
     payload:GetRatingReq,
    _: TokenPayload = Depends(require_role(UserRole.mechanic,UserRole.customer)),
    common_service: CommonService = Depends(get_common_service)):
      return await common_service.get_average_rating(payload.user_id)

@router.get("/get-mechanic-data")
async def get_mechanic_data(
     payload:GetRatingReq,
    _: TokenPayload = Depends(require_role(UserRole.mechanic,UserRole.customer)),
    common_service: CommonService = Depends(get_common_service)):
      return await common_service.get_mechanic_data(payload.user_id)

@router.get("/get-booking-progress/{booking_id}")
async def get_booking_progress(
     booking_id:str,
     credentials: TokenPayload = Depends(require_role(UserRole.mechanic,UserRole.customer)),
    common_service: CommonService = Depends(get_common_service)):
      return await common_service.get_bookings_progress(booking_id=booking_id,user_role=credentials.user_role)

@router.patch("/change-booking-status/{booking_id}")
async def accept_or_reject_booking(booking_id: str, booking_status: BookingStatusReq, credentials: TokenPayload = Depends(require_role(UserRole.mechanic,UserRole.customer)), common_service: CommonService = Depends(get_common_service)):

    if credentials.user_role == UserRole.mechanic.value and  booking_status.status not in [BookingStatus.canceled.value, BookingStatus.inspecting.value, BookingStatus.completed.value,BookingStatus.accepted.value, BookingStatus.rejected.value]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")
    
    if credentials.user_role == UserRole.customer.value and booking_status.status not in [BookingStatus.canceled.value, BookingStatus.completed.value, BookingStatus.paid.value, BookingStatus.arrived.value]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")

    return await common_service.change_booking_status(booking_id=booking_id, booking_status=booking_status.status, user_id=credentials.user_id, user_role=credentials.user_role)