from pydantic import BaseModel, EmailStr
from typing import Optional

class SimpleResponseSchema(BaseModel):
    message: str

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


class ResendCodeRequestSchema(BaseModel):
    user_id: str
class ResendCodeResponseSchema(BaseModel):
    message: str


class ForgotPasswordRequestSchema(BaseModel):
    email: EmailStr

class ForgotPasswordResponseSchema(BaseModel):
    message: str
    user_id: str


class VerifyResetPasswordRequestSchema(BaseModel):
    user_id: str
    code: str

class VerifyResetPasswordResponseSchema(BaseModel):
    message: str
    user_id: str
    token: str



class ResetPasswordRequestSchema(BaseModel):
    user_id: str
    password: str
    token: str


class UpdatePasswordRequestSchema(BaseModel):
    user_id: str
    new_password: str
    old_password: str