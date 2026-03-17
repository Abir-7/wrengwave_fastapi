from fastapi import APIRouter, Depends, HTTPException, status,File, Form,UploadFile
from typing import List,Optional
from app.database.dependencies import get_mechanic_service

from app.dependencies.auth import require_role
from app.database.models.user import UserRole
from app.schemas.auth import TokenPayload
from app.schemas.mechanic import MechanicDataResponse
from app.services.mechanic import MechanicService
from app.utils.file_upload import save_upload_file
from app.utils.data_format_helper.mechanic_data_helper import format_mechanic_data

router = APIRouter(prefix="/mechanic", tags=["common"])

@router.post("/save-mechanic-data", response_model=MechanicDataResponse
             )

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
   
    