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
from app.utils.data_format_helper.user_car_data_helper import format_cars_with_images



router = APIRouter(prefix="/user", tags=["user"])

@router.get("/me",response_model=UserWithProfileResponse)
async def get_me(
    current_user: TokenPayload = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)):

    return await user_service.get_user_profile(current_user.user_id)

@router.get("/{user_id}",response_model=UserWithProfileResponse)
async def get_user_profile(
    user_id: str,
    _: TokenPayload = Depends(require_role(UserRole.admin)),
    user_service: UserService = Depends(get_user_service)):
    return await user_service.get_user_profile(user_id)


@router.post("/add-cars",)
async def add_cars(
    cars_data: str = Form(...),
    images: List[UploadFile] = File(...),
    current_user: TokenPayload = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)):
    
    formated_cars = await format_cars_with_images(cars_data, images)

    return await user_service.save_user_car_data(current_user.user_id, formated_cars)

