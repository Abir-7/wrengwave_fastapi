import httpx
from fastapi import APIRouter, Form, File, UploadFile, HTTPException, Request

from typing import Optional, List
import asyncio

router = APIRouter(prefix="/car-issue", tags=["car_issue"])
AI_SERVER_URL = "http://localhost:5000"

# Reuse a single client across requests (connection pooling)
_client: httpx.AsyncClient | None = None

def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=5.0, read=60.0, write=30.0, pool=5.0),
            limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
        )
    return _client


@router.post("/{car_id}")
async def car_proxy(
    description: str = Form(...),
    images: Optional[List[UploadFile]] = File(None),
    audio: Optional[UploadFile] = File(None),
    service_date: str = Form(...),
):
    if images and len(images) > 3:
        raise HTTPException(status_code=400, detail="Maximum 3 images allowed")

    files: list[tuple] = [("description", (None, description))]

    async def read_upload(field: str, upload: UploadFile):
        data = await upload.read()
        return (field, (upload.filename, data, upload.content_type))

    tasks = []
    if images:
        tasks += [read_upload("images", img) for img in images]
    if audio:
        tasks.append(read_upload("audio", audio))

    # All reads fire in parallel
    results = await asyncio.gather(*tasks)
    files.extend(results)

    try:
        response = await get_client().post(
            f"{AI_SERVER_URL}/analysis/car",
            files=files,
        )
        response.raise_for_status()
        return response.json()

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI server timed out")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)