# utils/file_upload.py
import aiofiles, magic, uuid, os, logging, mimetypes
from fastapi import HTTPException

logger      = logging.getLogger(__name__)
UPLOAD_ROOT = "app/uploads"

MIME_ALIASES = {
    "audio/mp3":   "audio/mpeg",
    "audio/x-mp3": "audio/mpeg",
    "image/jpg":   "image/jpeg",
}

MIME_FOLDER_MAP = {
    "image/jpeg":      "images",
    "image/png":       "images",
    "image/webp":      "images",
    "audio/mpeg":      "audio",
    "audio/wav":       "audio",
    "application/pdf": "documents",
    "video/mp4":       "videos",
}

def _normalize_mime(mime: str) -> str:
    return MIME_ALIASES.get(mime, mime)

def _detect_mime(file_bytes: bytes) -> str:
    return _normalize_mime(magic.from_buffer(file_bytes[:2048], mime=True))

def _mime_to_ext(mime: str) -> str:
    """Get canonical extension from detected MIME."""
    ext = mimetypes.guess_extension(mime)
    if not ext:
        raise HTTPException(status_code=422, detail=f"Unsupported type: '{mime}'")
    # mimetypes can return .jpe for jpeg — normalize
    return ext.replace(".jpe", ".jpeg")

def _normalize_ext(ext: str) -> str:
    ext = ext.lower().strip()
    return ext if ext.startswith(".") else f".{ext}"

async def save_upload_file(
    file_bytes: bytes,
    max_size_mb: float,
    allowed_extensions: list[str],
) -> str:
    # 1. Size
    if len(file_bytes) > int(max_size_mb * 1024 * 1024):
        raise HTTPException(status_code=413, detail=f"Max size: {max_size_mb}MB")

    # 2. Detect real MIME from bytes
    actual_mime = _detect_mime(file_bytes)

    # 3. Derive extension from detected MIME — no user input
    actual_ext = _mime_to_ext(actual_mime)

    # 4. Whitelist check
    normalized_whitelist = [_normalize_ext(e) for e in allowed_extensions]
    if actual_ext not in normalized_whitelist:
        raise HTTPException(
            status_code=422,
            detail=f"File type '{actual_ext}' not allowed. Allowed: {', '.join(normalized_whitelist)}"
        )

    # 5. Supported folder?
    folder = MIME_FOLDER_MAP.get(actual_mime)
    if not folder:
        raise HTTPException(status_code=422, detail=f"Unsupported type: '{actual_mime}'")

    # 6. Save — extension from MIME, never from user
    safe_filename = f"{uuid.uuid4()}{actual_ext}"
    save_dir      = os.path.join(UPLOAD_ROOT, folder)
    os.makedirs(save_dir, exist_ok=True)
    file_path     = os.path.join(save_dir, safe_filename)

    try:
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_bytes)
    except OSError as e:
        logger.error(f"Write failed: {file_path} — {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save file")

    logger.info(f"Saved [{actual_mime}] → {file_path}")
    return f"/uploads/{folder}/{safe_filename}"