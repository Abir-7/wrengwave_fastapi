import jwt
import datetime
from typing import Optional
from app.database.models.enum import UserRole
from app.schemas.auth import TokenPayload

ALGORITHM = "HS256"


def create_jwt(user_id:  str, user_role: UserRole, user_email: str, expires_in_days: int, secret_key: str) -> str:
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "user_id": user_id,  
        "user_role": user_role.value,
        "user_email": user_email,
        "iat": int(now.timestamp()),  
        "exp": int((now + datetime.timedelta(days=expires_in_days)).timestamp()),  # ← same
    }
    return jwt.encode(payload, key=secret_key, algorithm=ALGORITHM)


def verify_jwt(token: str, secret_key: str) -> TokenPayload:
    try:
        payload = jwt.decode(token, key=secret_key, algorithms=[ALGORITHM])
        return TokenPayload(**payload)  
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")


def decode_jwt_unverified(token: str) -> Optional[TokenPayload]:
    try:
        payload = jwt.decode(token, options={"verify_signature": False}, algorithms=[ALGORITHM])  
        return TokenPayload(**payload)   
    except jwt.DecodeError:
        return None