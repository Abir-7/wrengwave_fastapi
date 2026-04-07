import asyncio
import stripe
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.service_booking import CarBookingService
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from app.database.models.payment import Payment
from fastapi import HTTPException
from app.database.models.enum import PaymentStatus
from fastapi.responses import JSONResponse
from stripe import AccountLink, Account
from app.schemas.payment import ConnectAccountResponse
from app.database.models import User
stripe.api_key = settings.STRIPE_SECRET_KEY

APP_FEE_PERCENT = 0.05  # 5%

WEBHOOK_HANDLERS = {
    "payment_intent.succeeded",
    "payment_intent.payment_failed",
    "payment_intent.canceled",
    "payment_intent.processing",
    "charge.dispute.created",
}


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_payment_intent(
        self,
        booking_id: str,
        currency: str = "usd",
    ) -> stripe.PaymentIntent:

     
        result = await self.db.execute(
            select(CarBookingService)
            .where(CarBookingService.id == booking_id)
            .options(
                joinedload(CarBookingService.service_price_details),
                joinedload(CarBookingService.mechanic),
            )
        )
        booking_data = result.scalar_one_or_none()

        if not booking_data:
            raise HTTPException(status_code=404, detail="Booking not found")
        if not booking_data.service_price_details:
            raise HTTPException(status_code=404, detail="Service price details not found")
        if not booking_data.mechanic:
            raise HTTPException(status_code=404, detail="Mechanic not found")

        mechanic_stripe_account_id = booking_data.mechanic.stripe_account_id
        if not mechanic_stripe_account_id:
            raise HTTPException(status_code=400, detail="Mechanic has no Stripe account")

        # 2. Calculate amounts (all in cents)
        base_amount = int(booking_data.service_price_details.total_price * 100)
        app_fee     = int(base_amount * APP_FEE_PERCENT)  


        loop = asyncio.get_running_loop()

        try:
            intent: stripe.PaymentIntent = await loop.run_in_executor(
                None,
                lambda: stripe.PaymentIntent.create(
                    amount=base_amount,
                    currency=currency,
                    payment_method_types=["card"],
                    application_fee_amount=app_fee,
                    transfer_data={"destination": mechanic_stripe_account_id},
                    metadata={
                        "booking_id":       booking_id,
                        "app_fee_cents":    str(app_fee),
                        "app_fee_percent":  str(APP_FEE_PERCENT),
                    },
                ),
            )
        except stripe.error.CardError as e:
            raise HTTPException(status_code=402, detail=e.user_message or str(e)) from e
        except stripe.error.InvalidRequestError as e:
            raise HTTPException(status_code=400, detail=e.user_message or str(e)) from e
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=502, detail=f"Stripe error: {e.user_message or str(e)}"
            ) from e

        # 4. Persist payment only after Stripe succeeds
        new_payment = Payment(
            amount=base_amount,
            app_fee=app_fee,                        
            booking_id=booking_id,
            currency=currency,
            customer_id=booking_data.booked_by,
            mechanic_id=booking_data.mechanic_id,
            status=PaymentStatus.UNPAID,
            payment_intent_id=intent.id,
        )
        self.db.add(new_payment)

        try:
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="Failed to save payment record") from e

        return intent
    


    async def connect_mechanic_stripe(
    self,
    mechanic_id: str,
    return_url: str,
    refresh_url: str,
) -> ConnectAccountResponse:
        
        loop = asyncio.get_event_loop()

        result=await self.db.execute(select(User).where(User.id == mechanic_id))
        mechanic = result.scalar_one_or_none()
        if not mechanic:
            raise ValueError(f"Mechanic {mechanic_id} not found")

        email = mechanic.email

        try:
            # Step 1: Create Stripe Express account
            account: Account = await loop.run_in_executor(
                None,
                lambda: stripe.Account.create(
                    type="express",
                    email=email,
                    capabilities={
                        "card_payments": {"requested": True},
                        "transfers": {"requested": True},
                    },
                ),
            )

            # Step 2: Generate onboarding link
            account_link: AccountLink = await loop.run_in_executor(
                None,
                lambda: stripe.AccountLink.create(
                    account=account.id,
                    refresh_url=refresh_url,
                    return_url=return_url,
                    type="account_onboarding",
                ),
            )

            # Step 3: Save stripe_account_id to mechanic record
            mechanic.stripe_account_id = account.id
            await self.db.commit()
            await self.db.refresh(mechanic)

            return ConnectAccountResponse(
                stripe_account_id=account.id,
                onboarding_url=account_link.url,
            )

        except stripe.error.StripeError as e:
            raise stripe.error.StripeError(f"Stripe error: {e.user_message}") from e


    async def get_connect_account(self, account_id: str) -> Account:
        """Retrieve a mechanic's Stripe account to check onboarding status."""
        loop = asyncio.get_event_loop()
        try:
            account: Account = await loop.run_in_executor(
                None,
                lambda: stripe.Account.retrieve(account_id),
            )
            return account
        except stripe.error.StripeError as e:
            raise stripe.error.StripeError(f"Stripe error: {e.user_message}") from e






    async def handle_webhook(self, payload: bytes, sig_header: str | None) -> JSONResponse:

            
            if not sig_header:
                raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

            loop = asyncio.get_running_loop()
            try:
                event = await loop.run_in_executor(
                    None,
                    lambda: stripe.Webhook.construct_event(
                        payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
                    ),
                )
            except stripe.error.SignatureVerificationError:
                raise HTTPException(status_code=400, detail="Invalid Stripe signature")
            except Exception:
                raise HTTPException(status_code=400, detail="Malformed webhook payload")

            event_type: str       = event["type"]
            event_obj:  dict      = event["data"]["object"]

            if event_type not in WEBHOOK_HANDLERS:
                return JSONResponse({"received": True, "handled": False})

            # 4. Dispatch
            handler_map = {
                "payment_intent.succeeded":      self._on_payment_succeeded,
                "payment_intent.payment_failed": self._on_payment_failed,
                "payment_intent.canceled":       self._on_payment_canceled,
                "payment_intent.processing":     self._on_payment_processing,
                "charge.dispute.created":        self._on_dispute_created,
            }

            handler = handler_map.get(event_type)
            if handler:
                await handler(event_obj)

            return JSONResponse({"received": True, "handled": True})

    # ─────────────────────────────────────────────────────────────────────────
    # SHARED DB HELPER
    # ─────────────────────────────────────────────────────────────────────────
    async def _get_payment(self, payment_intent_id: str) -> Payment | None:
        result = await self.db.execute(
            select(Payment).where(Payment.payment_intent_id == payment_intent_id)
        )
        return result.scalar_one_or_none()

    # ─────────────────────────────────────────────────────────────────────────
    # EVENT HANDLERS
    # ─────────────────────────────────────────────────────────────────────────
    async def _on_payment_succeeded(self, intent: dict) -> None:
        payment = await self._get_payment(intent["id"])
        if not payment:
            return

        payment.status  = PaymentStatus.PAID
      
        await self.db.commit()

    async def _on_payment_failed(self, intent: dict) -> None:
        payment = await self._get_payment(intent["id"])
        if not payment:
            return

        payment.status         = PaymentStatus.FAILED
       
        await self.db.commit()

    async def _on_payment_canceled(self, intent: dict) -> None:
        payment = await self._get_payment(intent["id"])
        if not payment:
            return

        payment.status = PaymentStatus.CANCELLED
        await self.db.commit()

    async def _on_payment_processing(self, intent: dict) -> None:
        payment = await self._get_payment(intent["id"])
        if not payment:
            return

        payment.status = PaymentStatus.PROCESSING
        await self.db.commit()

    async def _on_dispute_created(self, charge: dict) -> None:

        payment_intent_id = charge.get("payment_intent")
        if not payment_intent_id:
            return

        payment = await self._get_payment(payment_intent_id)
        if not payment:
            return

        payment.status = PaymentStatus.DISPUTED
        await self.db.commit()


