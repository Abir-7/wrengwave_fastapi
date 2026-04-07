from fastapi import APIRouter,status
from app.services.payment_service import  PaymentService
from stripe import PaymentIntent
from fastapi import Request, Depends
from app.database.dependencies import get_payment_service
from app.core.config import settings
from app.schemas.payment import ConnectAccountRequest, ConnectAccountResponse,AccountStatusResponse

router = APIRouter(prefix="/payments")


@router.post("/connect", response_model=ConnectAccountResponse, status_code=status.HTTP_201_CREATED)
async def connect_stripe_account(
    payload: ConnectAccountRequest,
    payment_service: PaymentService = Depends(get_payment_service),
):
        return_url = f"{settings.FRONTEND_URL}/mechanic/{payload.mechanic_id}/stripe/return"
        refresh_url = f"{settings.FRONTEND_URL}/mechanic/{payload.mechanic_id}/stripe/refresh"

        result = await payment_service.connect_mechanic_stripe(
        email=payload.email,
        mechanic_id=payload.mechanic_id,
        return_url=return_url,
        refresh_url=refresh_url,
        )
        
        return result

@router.get("/status/{stripe_account_id}", response_model=AccountStatusResponse)
async def get_account_status(
    stripe_account_id: str,
 payment_service: PaymentService = Depends(get_payment_service),
):
    """
    Step 2 — Check if the mechanic has completed onboarding.
    Poll this after the mechanic returns from the Stripe onboarding page.
    """
   
    account = await payment_service.get_connect_account(stripe_account_id)

    return AccountStatusResponse(
        stripe_account_id=account.id,
        charges_enabled=account.charges_enabled,
        payouts_enabled=account.payouts_enabled,
        details_submitted=account.details_submitted,
    )


@router.post("/create-payment-intent")
async def create_payment(
    payment_service: PaymentService = Depends(get_payment_service),
):
    intent: PaymentIntent = await payment_service.create_payment_intent(5000)  # $50.00
    return {
        "client_secret": intent.client_secret
    }

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    payment_service: PaymentService = Depends(get_payment_service),  # ✅ use dependency
):
    payload    = await request.body()
    sig_header = request.headers.get("stripe-signature")

    return await payment_service.handle_webhook(payload, sig_header)