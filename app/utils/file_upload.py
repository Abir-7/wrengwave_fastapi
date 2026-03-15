import os
import uuid
from fastapi import UploadFile

# Base uploads folder
# UPLOAD_ROOT = os.path.join(os.path.dirname(__file__), "uploads")
UPLOAD_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
# Supported extensions
IMAGE_EXT = {"jpg", "jpeg", "png", "gif", "webp"}
AUDIO_EXT = {"mp3", "wav", "m4a", "ogg"}
VIDEO_EXT = {"mp4", "mov", "avi", "mkv"}
DOC_EXT = {"pdf", "doc", "docx", "txt", "xlsx", "csv"}


def get_folder(ext: str) -> str:
    ext = ext.lower()
    if ext in IMAGE_EXT:
        return "images"
    elif ext in AUDIO_EXT:
        return "audio"
    elif ext in VIDEO_EXT:
        return "video"
    elif ext in DOC_EXT:
        return "documents"
    else:
        return "others"


async def save_upload_file(file: UploadFile) -> str:
    """
    Save uploaded file in uploads folder automatically based on type.
    Returns file path for serving (e.g., /uploads/images/<uuid>.png)
    """
    ext = file.filename.split(".")[-1].lower()
    folder = get_folder(ext)

    save_dir = os.path.join(UPLOAD_ROOT, folder)
    os.makedirs(save_dir, exist_ok=True)

    filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(save_dir, filename)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    # Return public path for FastAPI StaticFiles
    return f"/uploads/{folder}/{filename}"