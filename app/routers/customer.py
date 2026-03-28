from fastapi import APIRouter, Depends ,UploadFile, File, Form,Query
from app.database.dependencies import get_customer_service
from app.dependencies.auth import require_role
from app.schemas.auth import TokenPayload
from typing import Optional
from app.database.models.enum import UserRole
from typing import List
from app.utils.data_format_helper.customer_car_data_helper import format_cars_with_images
from app.services.customer import CustomerService
from app.schemas.customer import BookMechanic,UpdateBookingStatus

router = APIRouter(prefix="/customer", tags=["customer"])

@router.post("/add-cars",)
async def add_cars(
    cars_data: str = Form(...),
    images: List[UploadFile] = File(...),
    current_user: TokenPayload = Depends(require_role(UserRole.customer)),
    customer_service: CustomerService = Depends(get_customer_service)):

    formated_cars = await format_cars_with_images(cars_data, images)
    return await customer_service.save_user_car_data(current_user.user_id, formated_cars)

@router.get("/my-cars")
async def get_my_cars(current_user: TokenPayload = Depends(require_role(UserRole.customer)), customer_service: CustomerService = Depends(get_customer_service)):

    return await customer_service.get_users_cars(user_id=current_user.user_id)

@router.get("/my-bookings")
async def get_my_bookings(current_user: TokenPayload = Depends(require_role(UserRole.customer)), customer_service: CustomerService = Depends(get_customer_service)):

    return await customer_service.get_users_bookings(user_id=current_user.user_id)


@router.post("/car-issue/{car_id}")
async def car_proxy(
    
    car_id: str,
    description: str = Form(...),
    images: Optional[List[UploadFile]] = File(None),
    audios: Optional[List[UploadFile]] = File(None),  # ← changed
    service_date: str = Form(...),
    service_time: str = Form(...),
    latitude: Optional[float] = Form(None),   
    longitude: Optional[float] = Form(None),  
    current_user: TokenPayload = Depends(require_role(UserRole.customer)),
    customer_service: CustomerService = Depends(get_customer_service),
):
    return await customer_service.analyze_car_issue(
        user_id=current_user.user_id,
        car_id=car_id,        
        description=description,
        images=images,
        audios=audios,
        service_date=service_date,
        service_time=service_time,
        latitude=latitude,
        longitude=longitude
    )

@router.get("/get-mechanics")
async def get_mechanics(
    car_issue_id: str = Query(..., description="ID of the car issue"),
    current_user: TokenPayload = Depends(require_role(UserRole.customer)), customer_service: CustomerService = Depends(get_customer_service)):
    result=await customer_service.get_mechanics(car_issue_id=car_issue_id,user_id=current_user.user_id)
    return result

@router.post("/book-mechanic")
async def book_mechanic(
    payload:BookMechanic,
    current_user: TokenPayload = Depends(require_role(UserRole.customer)), customer_service: CustomerService = Depends(get_customer_service)):
    return await customer_service.book_mechanic(mechanic_id=payload.mechanic_id,car_issue_id=payload.car_issue_id,user_id=current_user.user_id)



