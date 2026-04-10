from fastapi import APIRouter, status, Request, Depends
from fastapi.responses import JSONResponse
from stripe import PaymentIntent

from app.core.config import settings
from app.database.dependencies import get_payment_service
from app.database.models.enum import UserRole
from app.dependencies.auth import require_role
from app.schemas.auth import TokenPayload
from app.schemas.payment import ConnectAccountResponse, AccountStatusResponse
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments")


@router.get("/connect", response_model=ConnectAccountResponse, status_code=status.HTTP_201_CREATED)
async def connect_stripe_account(
    credentials: TokenPayload = Depends(require_role(UserRole.mechanic)),
    payment_service: PaymentService = Depends(get_payment_service),
):
    return_url  = f"{settings.FRONTEND_URL}/mechanic/{credentials.user_id}/stripe/return"
    refresh_url = f"{settings.FRONTEND_URL}/mechanic/{credentials.user_id}/stripe/refresh"

    return await payment_service.connect_mechanic_stripe(
        mechanic_id=credentials.user_id,
        return_url=return_url,
        refresh_url=refresh_url,
    )


@router.get("/status/{stripe_account_id}", response_model=AccountStatusResponse)
async def get_account_status(
    stripe_account_id: str,
    payment_service: PaymentService = Depends(get_payment_service),
):
    account = await payment_service.get_connect_account(stripe_account_id)

    return AccountStatusResponse(
        stripe_account_id=account.id,
        charges_enabled=account.charges_enabled,
        payouts_enabled=account.payouts_enabled,
        details_submitted=account.details_submitted,
    )


# ✅ booking_id should come from the request body or path — not hardcoded
@router.post("/create-payment-intent/{booking_id}")
async def create_payment(
    booking_id: str,
    payment_service: PaymentService = Depends(get_payment_service),
):
    intent: PaymentIntent = await payment_service.create_payment_intent(booking_id=booking_id)
    return {"client_secret": intent.client_secret}


# ✅ webhook must NOT use auth dependency — Stripe calls this directly
@router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    payment_service: PaymentService = Depends(get_payment_service),
):
    payload    = await request.body()
    sig_header = request.headers.get("stripe-signature")
   
    return await payment_service.handle_webhook(payload, sig_header)