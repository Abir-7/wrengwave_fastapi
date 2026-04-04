from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import auth
from app.routers import common
from app.routers import customer
from app.routers import mechanic

from app.core.http_client import close_client
# In your main app (main.py)
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi import APIRouter
from app.core import exceptions
from sqlalchemy.exc import IntegrityError
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
api_router = APIRouter(prefix="/api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic (if needed)
    yield
    # Shutdown logic
    await close_client()

app = FastAPI(lifespan=lifespan)


app.add_exception_handler(Exception, exceptions.global_exception_handler)
app.add_exception_handler(HTTPException, exceptions.http_exception_handler)
app.add_exception_handler(RequestValidationError, exceptions.validation_exception_handler)
app.add_exception_handler(IntegrityError, exceptions.integrity_error_handler)



app.mount("/uploads", StaticFiles(directory="app/uploads"), name="uploads")

api_router.include_router(auth.router)
api_router.include_router(customer.router)
api_router.include_router(common.router)
api_router.include_router(mechanic.router)

app.include_router(api_router)


@app.get("/")
def read_root():
    return {"Hello": "World"}


