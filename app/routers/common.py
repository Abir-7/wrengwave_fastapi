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
from app.schemas.common import BookingStatusReq, CarDataCreate, CarDataResponse
from app.database.models.service_booking import BookingStatus
from fastapi import Query
from typing import List,Optional
from datetime import date
router = APIRouter(prefix="/common", tags=["common"])

@router.post("/car-data", response_model=CarDataResponse, status_code=status.HTTP_201_CREATED)
async def add_car_data(
    payload: CarDataCreate,
    _: TokenPayload = Depends(require_role(UserRole.admin)),
    common_service: CommonService = Depends(get_common_service)):
    return await common_service.add_car_data(brand=payload.brand, model=payload.model)

@router.get("/car-data")
async def get_all_car_data(
    common_service: CommonService = Depends(get_common_service)):
    return await common_service.get_all_car_data()

@router.get("/me",response_model=UserWithProfileResponse)
async def get_me(
    current_user: TokenPayload = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)):

    return await user_service.get_user_profile(current_user.user_id)


@router.post("/locations", response_model=UserLocationResponse)
async def update_user_location(
    payload:UserLocationCreate,

    common_service: CommonService = Depends(get_common_service)):
    return await common_service.update_location(payload.user_id, payload.latitude, payload.longitude , payload.address, payload.city, payload.country)

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

@router.get("/get-mechanic-data/{user_id}")
async def get_mechanic_data(
    user_id:str,
    _: TokenPayload = Depends(require_role(UserRole.mechanic,UserRole.customer)),
    common_service: CommonService = Depends(get_common_service)):
      return await common_service.get_mechanic_data(user_id)

@router.get("/all-bookings")
async def get_all_bookings(
    booking_status: Optional[List[BookingStatus]] = Query(default=None),
    service_date: Optional[date] = Query(default=None),
    _: TokenPayload = Depends(require_role(UserRole.mechanic,UserRole.customer)),
    common_service: CommonService = Depends(get_common_service)):
      return await common_service.get_all_bookings(booking_status=booking_status,user_role=_.user_role,user_id=_.user_id,service_date=service_date)

@router.get("/booking-details/{booking_id}")
async def get_booking_details(
     booking_id:str,
     credentials: TokenPayload = Depends(require_role(UserRole.mechanic,UserRole.customer)),
    common_service: CommonService = Depends(get_common_service)):
      return await common_service.get_booking_by_id(booking_id=booking_id,user_role=credentials.user_role,user_id=credentials.user_id)

@router.patch("/change-booking-status/{booking_id}")
async def change_booking_status(booking_id: str, booking_status: BookingStatusReq, credentials: TokenPayload = Depends(require_role(UserRole.mechanic,UserRole.customer)), common_service: CommonService = Depends(get_common_service)):


    if credentials.user_role == UserRole.mechanic.value and  booking_status.status not in [BookingStatus.canceled.value, BookingStatus.inspecting.value, BookingStatus.completed.value,BookingStatus.accepted.value,BookingStatus.rejected.value]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")
    
    if credentials.user_role == UserRole.customer.value and booking_status.status not in [BookingStatus.canceled.value, BookingStatus.completed.value, BookingStatus.paid.value, BookingStatus.arrived.value,BookingStatus.repairing.value]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")

    return await common_service.change_booking_status(booking_id=booking_id, booking_status=booking_status.status, user_id=credentials.user_id, user_role=credentials.user_role)