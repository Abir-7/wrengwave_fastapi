from fastapi import APIRouter, Depends, HTTPException, status , BackgroundTasks

from app.services.auth import AuthService
from app.schemas.auth import UserCreateSchema, SignUpResponseSchema, VerifyUserResponseSchema, VerifyUserRequestSchema, UserLoginSchema, UserLoginResponseSchema
from app.database.dependencies import get_auth_service
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=SignUpResponseSchema,status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreateSchema, background_tasks: BackgroundTasks,
   auth_service: AuthService = Depends(get_auth_service)  # 
    
    ):
    try:
        user = await auth_service.create_user(
            background_tasks,
            email=payload.email,
            password=payload.password,
            role=payload.role,
            full_name=payload.full_name,
            bio=payload.bio,
            avatar_url=payload.avatar_url,
        
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return SignUpResponseSchema(
        user_id=str(user.id),
        email=user.email,
        role=user.role,
    )

@router.post("/verify-user", response_model= VerifyUserResponseSchema)
async def verify_user_email(payload:VerifyUserRequestSchema, auth_service: AuthService = Depends(get_auth_service)):
    try:
        user = await auth_service.verify_user_email(payload.user_id, payload.code)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return VerifyUserResponseSchema(
        user_id=str(user.id),
        role=user.role,
    )

@router.post("/login")
async def user_login(payload: UserLoginSchema, auth_service: AuthService = Depends(get_auth_service))->UserLoginResponseSchema:
    try:
        user = await auth_service.user_login(payload.user_email, payload.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return UserLoginResponseSchema(
            user_id=str(user.id),
            role=user.role
    )