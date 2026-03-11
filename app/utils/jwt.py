import jwt
import datetime
from typing import Optional



ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 1


def create_jwt(user_id: int | str, user_role: str, user_email: str, expires_in_days: int = ACCESS_TOKEN_EXPIRE_DAYS, secret_key: str = "secret") -> str:

    payload = {
        "user_id": user_id,
        "user_role": user_role,
        "user_email": user_email,
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=expires_in_days),
    }

    token = jwt.encode(payload, SECRET_KEY=secret_key, algorithm=ALGORITHM)
    return token


def verify_jwt(token: str,secret_key: str) -> dict:

    payload = jwt.decode(token, SECRET_KEY=secret_key, algorithms=[ALGORITHM])
    return payload


def decode_jwt_unverified(token: str) -> Optional[dict]:

    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except jwt.DecodeError:
        return None