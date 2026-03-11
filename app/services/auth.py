from sqlalchemy.ext.asyncio import AsyncSession 

from sqlalchemy import select
from fastapi import BackgroundTasks
from app.database.models.user import User
from app.database.models.user_profile import UserProfile
from app.database.models.user_authentication import UserAuthentication, AuthStatus

from app.utils import hash
from sqlalchemy.exc import IntegrityError
from app.utils.code import generate_code
from datetime import datetime, timedelta, timezone
from app.utils.email import send_password_reset_email,send_verification_email
from app.utils.epx_time import is_expire

class AuthService:
    def __init__(self, db:AsyncSession):
        self.db=db

    async def create_user(self,
        background_tasks:BackgroundTasks,
        email: str,
        password: str,
        role: str = "customer",
        full_name: str | None = None,
        bio: str | None = None,
        avatar_url: str | None = None,
     
        )-> User:
        
        result = await self.db.execute(select(User).filter(User.email == email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            if existing_user.is_active:
                raise ValueError("Email already registered")

            # delete inactive user
            await self.db.delete(existing_user)
            await self.db.commit()


        new_user = User(email=email, role=role , hashed_password=hash.get_password_hash(password))
        self.db.add(new_user)

        try:
            await self.db.flush()
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError("Failed to create user") from e
        
        profile = UserProfile(
            user_id=new_user.id,
            full_name=full_name,
            bio=bio,
            avatar_url=avatar_url,
        )
        self.db.add(profile)

        try:
            await self.db.flush()
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError("Failed to create user") from e
        
        code = generate_code(length=4)
        expire_time = datetime.now(timezone.utc) + timedelta(minutes=10)
        auth = UserAuthentication(user_id=new_user.id, code=code,expire_time=expire_time)
        self.db.add(auth)
    

        try:
            await self.db.commit()
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError("Failed to create user profile") from e
        
        await self.db.refresh(new_user)
        # signup
        background_tasks.add_task(send_verification_email, new_user.email, code)

        # reset password
        # background_tasks.add_task(send_password_reset_email, new_user.email, code)

        return new_user
    
    async def verify_user_email(self, user_id: str, code: str):
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

        return user

    async def user_login(self, user_email: str, password: str)->User:
        result = await self.db.execute(select(User).filter(User.email == user_email))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        if not user.is_active:
            raise ValueError("User is not active")

        if not hash.verify_password(password, user.hashed_password):
            raise ValueError("Incorrect password")

        return user