from fastapi import FastAPI

from app.routers import auth
from app.routers import user
app = FastAPI()



app.include_router(auth.router)
app.include_router(user.router)
@app.get("/")
def read_root():
    return {"Hello": "World"}


