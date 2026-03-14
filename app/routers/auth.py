from fastapi import APIRouter, Depends, HTTPException, status , BackgroundTasks,Form, UploadFile, File

from app.services.auth import AuthService

from app.schemas.auth import UserCreateSchema, SignUpResponseSchema,  VerifyUserRequestSchema, UserLoginSchema, UserLoginResponseSchema, ForgotPasswordRequestSchema, ForgotPasswordResponseSchema , VerifyResetPasswordRequestSchema, VerifyResetPasswordResponseSchema, ResendCodeRequestSchema, ResendCodeResponseSchema , ResetPasswordRequestSchema, SimpleResponseSchema, UpdatePasswordRequestSchema

from app.database.dependencies import get_auth_service


from app.dependencies.auth import get_current_user ,require_role
from app.schemas.auth import TokenPayload

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


@router.post("/verify-user", response_model= UserLoginResponseSchema)
async def verify_user_email(payload:VerifyUserRequestSchema, auth_service: AuthService = Depends(get_auth_service)):
    try:
        result = await auth_service.verify_user_email(payload.user_id, payload.code)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return result


@router.post("/login")
async def user_login(payload: UserLoginSchema, auth_service: AuthService = Depends(get_auth_service))->UserLoginResponseSchema:
    try:
        result = await auth_service.user_login(payload.user_email, payload.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return result


@router.post("/resend-code" , response_model=ResendCodeResponseSchema)
async def resend_code(payload: ResendCodeRequestSchema, background_tasks: BackgroundTasks, auth_service: AuthService = Depends(get_auth_service))->ResendCodeResponseSchema:
    try:
        result = await auth_service.resend_code(payload.user_id,background_tasks=background_tasks) 
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return ResendCodeResponseSchema(message="Code resent successfully")


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequestSchema, background_tasks: BackgroundTasks, auth_service: AuthService = Depends(get_auth_service))->ForgotPasswordResponseSchema:
    try:
      result=  await auth_service.forgot_password(payload.email, background_tasks)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return ForgotPasswordResponseSchema(message="Password reset email sent", user_id=str(result.id))


@router.post("/verify-password-reset", response_model=VerifyResetPasswordResponseSchema)
async def verify_reset_password(payload:  VerifyResetPasswordRequestSchema, auth_service: AuthService = Depends(get_auth_service))->VerifyResetPasswordResponseSchema:
    try:
        result = await auth_service.verify_reset_password(user_id=payload.user_id, code=payload.code)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return VerifyResetPasswordResponseSchema(message="Password reset successfully", user_id=str(result.user_id), token=result.token)

@router.post("/reset-password",response_model=SimpleResponseSchema)
async def reset_password(payload: ResetPasswordRequestSchema, auth_service: AuthService = Depends(get_auth_service))->SimpleResponseSchema:
    try:
        await auth_service.reset_password(user_id=payload.user_id, password=payload.password,token=payload.token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return SimpleResponseSchema(message="Password reset successfully")

@router.post("/update-password",response_model=SimpleResponseSchema)
async def update_password(payload: UpdatePasswordRequestSchema, auth_service: AuthService = Depends(get_auth_service))->SimpleResponseSchema:
    try:
        await auth_service.update_password(user_id=payload.user_id, new_password=payload.new_password,old_password=payload.old_password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return SimpleResponseSchema(message="Password updated successfully")

@router.post("/update-profile", response_model=SimpleResponseSchema)
async def update_profile(
    _: TokenPayload = Depends(get_current_user),
 user_id: str | None = Form(None),
    full_name: str | None = Form(None),
    bio: str | None = Form(None),
    avatar: UploadFile | None = File(None),
    auth_service: AuthService = Depends(get_auth_service),
) -> SimpleResponseSchema:
    try:

        await auth_service.update_profile(
            user_id=user_id,
            full_name=full_name,
            bio=bio,
            avatar=avatar
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return SimpleResponseSchema(message="Profile updated successfully")
