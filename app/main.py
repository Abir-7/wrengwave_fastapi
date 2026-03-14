from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import auth
from app.routers import user
app = FastAPI()


app.mount("/uploads", StaticFiles(directory="app/uploads"), name="uploads")

app.include_router(auth.router)
app.include_router(user.router)

@app.get("/")
def read_root():
    return {"Hello": "World"}


