from sqlalchemy.ext.asyncio import AsyncSession 

from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload

from fastapi import BackgroundTasks,UploadFile
from app.database.models.user import User
from app.database.models.user_profile import UserProfile
from app.database.models.user_authentication import UserAuthentication, AuthStatus
from app.database.models.ratings import AverageRating
from app.utils import hash
from sqlalchemy.exc import IntegrityError
from app.utils.code import generate_code
from datetime import datetime, timedelta, timezone
from app.utils.email import send_password_reset_email,send_verification_email,resend_code_email
from app.utils.epx_time import is_expire
from app.schemas.auth import UserLoginResponseSchema
from app.utils.jwt import create_jwt
from app.core.config import settings
from app.utils.file_upload import save_upload_file
from app.utils.file_delete import delete_file
class AuthService:
    def __init__(self, db:AsyncSession):
        self.db=db


    async def create_user(
        self,
        background_tasks: BackgroundTasks,
        email: str,
        password: str,
        role: str = "customer",
        full_name: str | None = None,
        bio: str | None = None,
        avatar_url: str | None = None,
    ) -> User:
        
        # Check for existing user
        result = await self.db.execute(select(User).filter(User.email == email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            if existing_user.is_active:
                raise ValueError("Email already registered")
            await self.db.delete(existing_user)
            await self.db.commit()

        # Build all objects upfront
        new_user = User(
            email=email,
            role=role,
            hashed_password=hash.get_password_hash(password),
        )
        self.db.add(new_user)

        try:
            await self.db.flush()  # Get new_user.id before building dependents
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError("Email already registered") from e

        code = generate_code(length=4)
        expire_time = datetime.now(timezone.utc) + timedelta(minutes=10)

        self.db.add_all([
            UserProfile(user_id=new_user.id, full_name=full_name, bio=bio, avatar_url=avatar_url),
            UserAuthentication(user_id=new_user.id, code=code, expire_time=expire_time),
            AverageRating(user_id=new_user.id, user_type=role,avg_rating=0.0,total_rating=0),
        ])

        try:
            await self.db.commit()
        except IntegrityError as e:
            print(e)
            await self.db.rollback()
            raise ValueError("Failed to create user") from e

        await self.db.refresh(new_user)
        background_tasks.add_task(send_verification_email, new_user.email, code)

        return new_user

    async def verify_user_email(self, user_id: str, code: str)->UserLoginResponseSchema:
        result = await self.db.execute(
        select(UserAuthentication)
        .where(
        UserAuthentication.user_id == user_id,
        UserAuthentication.status == AuthStatus.pending
    )
        .order_by(UserAuthentication.created_at.desc())
        .limit(1)
    )
        auth = result.scalar_one_or_none()

        if not auth:
            raise ValueError("Verification code not found")

        if auth.expire_time and is_expire(auth.expire_time):
            auth.status=AuthStatus.expire
            await self.db.commit()
            raise ValueError("Verification code has expired")

        if auth.code != code:
            raise ValueError("Incorrect verification code")

        user = await self.db.get(User, user_id)
        user.is_active = True
        auth.status=AuthStatus.success
        await self.db.commit()

        access_token= create_jwt(user_email=user.email,user_id=str(user.id),user_role=user.role,expires_in_days=settings.ACCESS_TOKEN_EXPIRE_DAYS,secret_key=settings.ACCESS_SECRET_KEY)

        refresh_token= create_jwt(user_email=user.email,user_id=str(user.id),user_role=user.role,expires_in_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,secret_key=settings.REFRESH_SECRET_KEY)

        return UserLoginResponseSchema(user_id=str(user.id), role=user.role,access_token=access_token,refresh_token=refresh_token)


    async def user_login(self, user_email: str, password: str)->UserLoginResponseSchema:
        result = await self.db.execute(select(User).filter(User.email == user_email))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        if not user.is_active:
            raise ValueError("User is not active")

        if not hash.verify_password(password, user.hashed_password):
            raise ValueError("Incorrect password")
    
        
        access_token= create_jwt(user_email=user.email,user_id=str(user.id),user_role=user.role,expires_in_days=settings.ACCESS_TOKEN_EXPIRE_DAYS,secret_key=settings.ACCESS_SECRET_KEY)

        refresh_token= create_jwt(user_email=user.email,user_id=str(user.id),user_role=user.role,expires_in_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,secret_key=settings.REFRESH_SECRET_KEY)

        return UserLoginResponseSchema(user_id=str(user.id), role=user.role,access_token=access_token,refresh_token=refresh_token)
    

    async def resend_code(self, user_id: str, background_tasks:BackgroundTasks)->None:
        result = await self.db.execute(select(UserAuthentication).where(UserAuthentication.user_id == user_id).order_by(UserAuthentication.created_at.desc())
        .limit(1))
        user_authentication = result.scalar_one_or_none()

        if not user_authentication:
            raise ValueError("User authentication not found")
        
        user=await self.db.get(User,user_authentication.user_id)
        if not user:
            raise ValueError("User not found")

        if  user_authentication.status == AuthStatus.pending:
            user_authentication.status = AuthStatus.expire

    
        code = generate_code(length=4)
        expire_time = datetime.now(timezone.utc) + timedelta(minutes=10)
        auth = UserAuthentication(user_id=user_authentication.user_id, code=code,expire_time=expire_time)
        self.db.add(auth)

        try:
            await self.db.commit()
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError("Failed to send verification email") from e
        

        background_tasks.add_task(resend_code_email, user.email, code)
            
       

    async def forgot_password(self, email: str, background_tasks:BackgroundTasks)->User:
        result = await self.db.execute(select(User).filter(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        if not user.is_active:
            raise ValueError("User is not active")

        code = generate_code(length=4)
        expire_time = datetime.now(timezone.utc) + timedelta(minutes=10)
        auth = UserAuthentication(user_id=user.id, code=code,expire_time=expire_time)
        self.db.add(auth)

        try:
            await self.db.commit()
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError("Failed to send password reset email") from e

        background_tasks.add_task(send_password_reset_email, user.email, code)

        return user
    

    async def verify_reset_password(self, user_id: str, code: str) -> UserAuthentication:
        result = await self.db.execute(
            select(UserAuthentication)
            .where(
                UserAuthentication.user_id == user_id,
                UserAuthentication.status == AuthStatus.pending
            )
            .order_by(UserAuthentication.created_at.desc())
            .limit(1)
        )
        auth = result.scalar_one_or_none()

        if not auth:
            raise ValueError("Verification code not found")

        if auth.expire_time and is_expire(auth.expire_time):
            auth.status = AuthStatus.expire
            await self.db.commit()
            raise ValueError("Verification code has expired")

        if auth.code != code:
            raise ValueError("Incorrect verification code")
    
        user = await self.db.get(User, user_id)
        if not user:
            raise ValueError("User not found")

        token = create_jwt(
            user_email=user.email,
            user_id=str(user.id),
            user_role=user.role,
            expires_in_days=settings.ACCESS_TOKEN_EXPIRE_DAYS,
            secret_key=settings.ACCESS_SECRET_KEY
        )
        expire_time = datetime.now(timezone.utc) + timedelta(minutes=10)
        
        auth.status = AuthStatus.success
        new_auth = UserAuthentication(user_id=user.id, token=token, expire_time=expire_time)
        self.db.add(new_auth)

        try:
            await self.db.commit()
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError("Failed to verify. Please try again") from e

        return new_auth
    

    async def reset_password(self, user_id: str, password: str,token: str)->None:
        user_authentication = await self.db.execute(select(UserAuthentication).where(UserAuthentication.token == token,UserAuthentication.status == AuthStatus.pending,UserAuthentication.user_id == user_id))

        auth = user_authentication.scalar_one_or_none()

        if not auth:
            raise ValueError("Verification token not found")
        
        if auth.status == AuthStatus.expire:
            raise ValueError("Verification token has expired")

        if auth.expire_time and is_expire(auth.expire_time):
            auth.status = AuthStatus.expire
            await self.db.commit()
            raise ValueError("Verification token has expired")
        
        result = await self.db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        user.hashed_password = hash.get_password_hash(password)
        await self.db.commit()

    async def update_password(self, user_id: str, new_password: str,old_password: str)->None:
        result = await self.db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        if not hash.verify_password(old_password, user.hashed_password):
            raise ValueError("Incorrect old password")

        user.hashed_password = hash.get_password_hash(new_password)
        await self.db.commit()

    async def update_profile(
    self,

    user_id: str,
    full_name: str,
    bio: str,
    avatar: UploadFile ,
) -> None:
        print(user_id)
    # Fetch profile first before doing any I/O side effects
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise ValueError(f"User not found: {user_id}")

        # Only upload avatar if provided, avoiding unnecessary I/O
        old_avatar = profile.avatar_url
        if avatar is not None:
            new_avatar_url = await save_upload_file(avatar)
            profile.avatar_url =  new_avatar_url
        
       

        profile.full_name = full_name
        profile.bio = bio

        await self.db.commit()
        if old_avatar and new_avatar_url:
            print(delete_file(
                old_avatar
            ))
    
    async def new_access_token(self, user_id: str)->str:
        result = await self.db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")
        access_token= create_jwt(user_email=user.email,user_id=str(user.id),user_role=user.role,expires_in_days=settings.ACCESS_TOKEN_EXPIRE_DAYS,secret_key=settings.ACCESS_SECRET_KEY)
        return {"access_token":access_token}

   