from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.jwt import verify_jwt
from app.core.config import settings
from fastapi import Depends, HTTPException, status
from app.schemas.auth import TokenPayload
from app.database.models.user import UserRole


bearer_scheme = HTTPBearer()
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> TokenPayload:
    return verify_jwt(secret_key=settings.ACCESS_SECRET_KEY, token=credentials.credentials)


def require_role(*allowed_roles: UserRole):
    def dependency(current_user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
    
        if UserRole(current_user.user_role) not in allowed_roles: 
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {list(allowed_roles)}"
            )
        return current_user
    return dependency