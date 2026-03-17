from fastapi import APIRouter, Depends ,UploadFile, File, Form,HTTPException,status
from app.database.dependencies import get_user_service 
from app.services.user import UserService
from app.dependencies.auth import get_current_user ,require_role
from app.schemas.auth import TokenPayload
from app.schemas.user import UserWithProfileResponse
from app.database.models.user import UserRole
from typing import List, Optional
import json
from app.utils.file_upload import save_upload_file
from app.utils.data_format_helper.customer_car_data_helper import format_cars_with_images



router = APIRouter(prefix="/customer", tags=["customer"])



@router.post("/add-cars",)
async def add_cars(
    cars_data: str = Form(...),
    images: List[UploadFile] = File(...),
    current_user: TokenPayload = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)):
    
    formated_cars = await format_cars_with_images(cars_data, images)

    return await user_service.save_user_car_data(current_user.user_id, formated_cars)

