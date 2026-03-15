from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.services.auth import AuthService
from app.services.user import UserService
from app.services.common import CommonService

def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)

def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)


def get_common_service(db: AsyncSession = Depends(get_db)) -> CommonService:
    return CommonService(db)