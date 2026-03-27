from fastapi import APIRouter, Depends, HTTPException, status,File, Form,UploadFile,Query
from typing import List,Optional
from app.database.dependencies import get_mechanic_service

from app.dependencies.auth import require_role
from app.database.models.enum import UserRole
from app.schemas.auth import TokenPayload
from app.schemas.mechanic import MechanicDataResponse
from app.schemas.common import BookingStatusReq
from app.services.mechanic import MechanicService
from app.utils.file_upload import save_upload_file
from app.utils.data_format_helper.mechanic_data_helper import format_mechanic_data
from app.database.models.service_booking import BookingStatus

router = APIRouter(prefix="/mechanic", tags=["common"])

@router.post("/save-mechanic-data", response_model=MechanicDataResponse)
async def save_mechanic_data(
    mechanic_data: str = Form(...),
    national_id_image: Optional[UploadFile] = File(None),
    certificate_images: Optional[ List[UploadFile]] = File(None),
    profile_image: Optional[UploadFile] = File(None),
    credentials: TokenPayload = Depends(require_role(UserRole.mechanic)), mechanic_service: 
    MechanicService = Depends(get_mechanic_service)):

    try:
        data=await format_mechanic_data(mechanic_data, certificate_images,national_id_image)
        profile_image_url=None
        if profile_image:
            profile_image_url=await save_upload_file(profile_image)
        result= await mechanic_service.save_mechanic_data(credentials.user_id,data,profile_image_url)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))        
   
@router.get("/get-all-booking")
async def get_mechanics_all_booking_services(
    booking_status: BookingStatus = Query(...), 
    credentials: TokenPayload = Depends(require_role(UserRole.mechanic)),
    mechanic_service: MechanicService = Depends(get_mechanic_service)
):
    return await mechanic_service.get_mechanics_all_booking_services(mechanic_id=credentials.user_id, booking_status=booking_status)

@router.get("/get-booking-details/{booking_id}")
async def get_booking_details(booking_id: str, _: TokenPayload = Depends(require_role(UserRole.mechanic)), mechanic_service: MechanicService = Depends(get_mechanic_service)):
    return await mechanic_service.booking_detais(booking_id=booking_id)

@router.patch("/accept-or-reject-booking/{booking_id}")
async def accept_or_reject_booking(booking_id: str, booking_status: BookingStatusReq, credentials: TokenPayload = Depends(require_role(UserRole.mechanic)), mechanic_service: MechanicService = Depends(get_mechanic_service)):

    if booking_status.status not in [BookingStatus.accepted.value, BookingStatus.rejected.value]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")

    return await mechanic_service.accept_or_reject_booking(booking_id=booking_id, booking_status=booking_status.status, mechanic_id=credentials.user_id)