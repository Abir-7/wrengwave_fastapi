import jwt
import datetime
from typing import Optional
from app.database.models.user import UserRole


ALGORITHM = "HS256"


def create_jwt(user_id: int | str, user_role:UserRole , user_email: str, expires_in_days: int , secret_key: str ) -> str:
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "user_id": user_id,
        "user_role": user_role.value,
        "user_email": user_email,
        "iat": now,
        "exp": now + datetime.timedelta(days=expires_in_days),
    }

    token = jwt.encode(payload, key=secret_key, algorithm=ALGORITHM)
    return token


def verify_jwt(token: str,secret_key: str) -> dict:

    payload = jwt.decode(token, key=secret_key, algorithms=[ALGORITHM])
    return payload


def decode_jwt_unverified(token: str) -> Optional[dict]:

    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except jwt.DecodeError:
        return None