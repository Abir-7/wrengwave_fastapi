from fastapi import APIRouter
from app.services.payment_service import  PaymentService
from stripe import PaymentIntent
router = APIRouter(prefix="/payments")


@router.post("/create-payment-intent")
async def create_payment():
    intent: PaymentIntent = await PaymentService.create_payment_intent(5000)  # $50.00
    return {
        "client_secret": intent.client_secret
    }