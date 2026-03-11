from pydantic import BaseModel, EmailStr
from typing import Optional

class TokenPayload(BaseModel):
    user_id:  str
    user_role: str  # or UserRole if you want strict typing
    user_email: str
    iat: int
    exp: int


class UserCreateSchema(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    role: str | None = "customer"  

class SignUpResponseSchema(BaseModel):
    user_id: str
    email: EmailStr
    role: str


class VerifyUserRequestSchema(BaseModel):
    user_id: str
    code: str




class UserLoginSchema(BaseModel):
    user_email: EmailStr
    password: str

class UserLoginResponseSchema(BaseModel):
    user_id: str
    role: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None