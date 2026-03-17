from fastapi import HTTPException, status
from typing import List,  Optional
from fastapi import UploadFile
import json
from app.utils.file_upload import save_upload_file
from app.schemas.mechanic import MechanicBaseData
async def format_mechanic_data(mechanic_data: str, certificates_data: Optional[List[UploadFile]],national_id_data: Optional[UploadFile]) -> MechanicBaseData:

    try:
        data = json.loads(mechanic_data)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON in mechanic_data"
        )

    certificates = []
    try:
        if certificates_data:
            for file in certificates_data:
                url = await save_upload_file(file)
                certificates.append({
                    "certificate_image_url": url,
                    "certificate_image_id": url
                })
        data["certificates"] = certificates


        if national_id_data:
            url = await save_upload_file(national_id_data)
            data["national_id_image_url"] = url
            data["national_image_id"] = url
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing files: {str(e)}"
        )

    return MechanicBaseData(**data)
    