from typing import List, Dict, Optional
from fastapi import UploadFile, HTTPException, status
import json
from app.utils.file_upload import save_upload_file

async def format_cars_with_images(cars_data: str, images: Optional[List[UploadFile]]) -> List[Dict]:

    if not images or len(images) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No images provided")

    try:
        cars = json.loads(cars_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid cars_data JSON")

    if len(cars) != len(images):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Number of cars and images do not match")

    formatted_cars = []
    for car, image in zip(cars, images):
        url = await save_upload_file(image)  # your existing async image saving function
        car["image_url"] = url
        car["image_id"] = url
        formatted_cars.append(car)

    return formatted_cars