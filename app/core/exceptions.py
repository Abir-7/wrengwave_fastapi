import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)


# 🔴 Generic fallback (last line of defense)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error: {exc}")

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal Server Error",
        },
    )


# 🔵 HTTPException (your manual raises)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
        },
    )


# 🟡 Validation errors (Pydantic)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Validation Error",
            "errors": exc.errors(),
        },
    )


# 🟣 Database errors (IMPORTANT for your case)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    logger.error(f"Integrity error: {exc}")

    error_str = str(exc.orig).lower()

    # 👇 Customize messages based on error type
    if "foreign key constraint" in error_str:
        message = "Invalid reference ID (related resource not found)"
    elif "unique constraint" in error_str:
        message = "Duplicate entry (already exists)"
    elif "not-null constraint" in error_str:
        message = "Missing required field"
    else:
        message = "Database integrity error"

    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "message": message,
        },
    )