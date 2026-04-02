from fastapi import APIRouter, Depends, HTTPException, status,File, Form,UploadFile,Query
from typing import List,Optional
from app.database.dependencies import get_mechanic_service

from app.dependencies.auth import require_role
from app.database.models.enum import UserRole
from app.schemas.auth import TokenPayload
from app.schemas.mechanic import MechanicDataResponse,MechanicDataRequest
from app.schemas.common import BookingStatusReq
from app.services.mechanic import MechanicService
from app.utils.file_upload import save_upload_file

from app.database.models.service_booking import BookingStatus

router = APIRouter(prefix="/mechanic", tags=["common"])

@router.post("/save-mechanic-image-data")
async def save_mechanic_image_data(
    national_id_image: Optional[UploadFile] = File(None),
    certificate_images: Optional[ List[UploadFile]] = File(None),
    profile_image: Optional[UploadFile] = File(None),
    credentials: TokenPayload = Depends(require_role(UserRole.mechanic)), mechanic_service: 
    MechanicService = Depends(get_mechanic_service)):
    try:
        return await mechanic_service.save_mechanic_image_data(credentials.user_id,national_id_image,certificate_images,profile_image)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/save-mechanic-data", response_model=MechanicDataResponse)
async def save_mechanic_data(
    mechanic_data: MechanicDataRequest,
    credentials: TokenPayload = Depends(require_role(UserRole.mechanic)), mechanic_service: 
    MechanicService = Depends(get_mechanic_service)):
    try:
        result= await mechanic_service.save_mechanic_data(mechanic_id=credentials.user_id,mechanic_data=mechanic_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))        
    
@router.post("/add-price-details/{booking_id}")
async def add_price_details(booking_id: str, price_details: dict, _: TokenPayload = Depends(require_role(UserRole.mechanic)), mechanic_service: MechanicService = Depends(get_mechanic_service)):
    return await mechanic_service.add_price_details(booking_id=booking_id, price_details=price_details, mechanic_id=_.user_id)