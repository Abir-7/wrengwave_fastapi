from fastapi import APIRouter, Depends ,UploadFile, File, Form
from app.database.dependencies import get_user_service 
from app.dependencies.auth import require_role
from app.schemas.auth import TokenPayload

from app.database.models.user import UserRole
from typing import List
from app.utils.data_format_helper.customer_car_data_helper import format_cars_with_images
from app.services.customer import CustomerService


router = APIRouter(prefix="/customer", tags=["customer"])


@router.post("/add-cars",)
async def add_cars(
    cars_data: str = Form(...),
    images: List[UploadFile] = File(...),
    current_user: TokenPayload = Depends(require_role(UserRole.customer)),
    customer_service: CustomerService = Depends(get_user_service)):

    formated_cars = await format_cars_with_images(cars_data, images)
    return await customer_service.save_user_car_data(current_user.user_id, formated_cars)

@router.get("/my-cars")
async def get_my_cars(current_user: TokenPayload = Depends(require_role(UserRole.customer)), customer_service: CustomerService = Depends(get_user_service)):
    pass