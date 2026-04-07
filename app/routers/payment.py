from fastapi import APIRouter
from app.services.payment_service import  PaymentService
from stripe import PaymentIntent
from fastapi import Request, Depends
from app.database.dependencies import get_payment_service
router = APIRouter(prefix="/payments")


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