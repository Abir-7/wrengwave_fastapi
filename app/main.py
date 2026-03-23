from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import auth
from app.routers import common
from app.routers import customer
from app.routers import mechanic
from app.routers import car_service
from app.core.http_client import close_client
# In your main app (main.py)
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic (if needed)
    yield
    # Shutdown logic
    await close_client()


app = FastAPI(lifespan=lifespan)



app.mount("/uploads", StaticFiles(directory="app/uploads"), name="uploads")

app.include_router(auth.router)
app.include_router(customer.router)
app.include_router(common.router)
app.include_router(mechanic.router)
app.include_router(car_service.router)

@app.get("/")
def read_root():
    return {"Hello": "World"}


