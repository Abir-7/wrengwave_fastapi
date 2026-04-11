import asyncio
import logging

import stripe
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from stripe import Account, AccountLink

from app.core.config import settings
from app.database.models import User
from app.database.models.enum import PaymentStatus
from app.database.models.mechanic_stripe import MechanicStripe
from app.database.models.payment import Payment
from app.database.models.service_booking import CarBookingService
from app.schemas.payment import ConnectAccountResponse

stripe.api_key = settings.STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)

APP_FEE_PERCENT = 0.05  # 5%

WEBHOOK_HANDLERS = {
    "account.updated",
    "application_fee.created",
    "charge.refunded",
    "payment_intent.succeeded",
    "payment_intent.payment_failed",
    "transfer.created",
}


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ─────────────────────────────────────────────────────────────────────────
    # CREATE PAYMENT INTENT
    # ─────────────────────────────────────────────────────────────────────────

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

        # ✅ Get stripe account from MechanicStripe table
        stripe_result = await self.db.execute(
            select(MechanicStripe).where(
                MechanicStripe.mechanic_id == booking_data.mechanic_id
            )
        )
        mechanic_stripe = stripe_result.scalar_one_or_none()

        if not mechanic_stripe or not mechanic_stripe.stripe_account_id:
            raise HTTPException(status_code=400, detail="Mechanic has no Stripe account")

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
                    transfer_data={"destination": mechanic_stripe.stripe_account_id},
                    metadata={
                        "booking_id":      booking_id,
                        "app_fee_cents":   str(app_fee),
                        "app_fee_percent": str(APP_FEE_PERCENT),
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
        print(PaymentStatus.UNPAID.value,PaymentStatus.UNPAID)
        new_payment = Payment(
            amount=base_amount,
            platform_fee=app_fee,
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

    # ─────────────────────────────────────────────────────────────────────────
    # CONNECT MECHANIC STRIPE
    # ─────────────────────────────────────────────────────────────────────────

    async def connect_mechanic_stripe(
        self,
        mechanic_id: str,
        return_url: str,
        refresh_url: str,
    ) -> ConnectAccountResponse:

        loop = asyncio.get_event_loop()

        result = await self.db.execute(select(User).where(User.id == mechanic_id))
        mechanic = result.scalar_one_or_none()
        if not mechanic:
            raise HTTPException(status_code=404, detail="Mechanic not found")

        stripe_result = await self.db.execute(
            select(MechanicStripe).where(MechanicStripe.mechanic_id == mechanic.id)
        )
        mechanic_stripe = stripe_result.scalar_one_or_none()

        try:
            if mechanic_stripe and mechanic_stripe.stripe_account_id:
                account: Account = await loop.run_in_executor(
                    None,
                    lambda: stripe.Account.retrieve(mechanic_stripe.stripe_account_id),
                )
                if account.details_submitted:
                    # ✅ Return 400 instead of raising ValueError
                    raise HTTPException(
                        status_code=400,
                        detail="Mechanic has already completed Stripe onboarding."
                    )

            else:
                account: Account = await loop.run_in_executor(
                    None,
                    lambda: stripe.Account.create(
                        type="express",
                        email=mechanic.email,
                        capabilities={
                            "card_payments": {"requested": True},
                            "transfers":     {"requested": True},
                        },
                    ),
                )

                if mechanic_stripe:
                    mechanic_stripe.stripe_account_id = account.id
                else:
                    mechanic_stripe = MechanicStripe(
                        mechanic_id=mechanic.id,
                        stripe_account_id=account.id,
                    )
                    self.db.add(mechanic_stripe)

                await self.db.commit()
                await self.db.refresh(mechanic_stripe)

            account_link: AccountLink = await loop.run_in_executor(
                None,
                lambda: stripe.AccountLink.create(
                    account=mechanic_stripe.stripe_account_id,
                    refresh_url=refresh_url,
                    return_url=return_url,
                    type="account_onboarding",
                ),
            )

            return ConnectAccountResponse(
                stripe_account_id=mechanic_stripe.stripe_account_id,
                onboarding_url=account_link.url,
            )

        except HTTPException:
            raise  # ✅ always re-raise HTTPException so FastAPI handles it correctly

        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=502,
                detail=f"Stripe error: {e.user_message or str(e)}"
            ) from e
    # ─────────────────────────────────────────────────────────────────────────
    # GET CONNECT ACCOUNT
    # ─────────────────────────────────────────────────────────────────────────

    async def get_connect_account(self, account_id: str) -> Account:
        loop = asyncio.get_event_loop()
        try:
            account: Account = await loop.run_in_executor(
                None,
                lambda: stripe.Account.retrieve(account_id),
            )
            return account
        except stripe.error.StripeError as e:
            raise stripe.error.StripeError(f"Stripe error: {e.user_message}") from e

    # ─────────────────────────────────────────────────────────────────────────
    # WEBHOOK
    # ─────────────────────────────────────────────────────────────────────────

    async def handle_webhook(self, payload: bytes, sig_header: str | None) -> JSONResponse:

        if not sig_header:
            raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

        loop = asyncio.get_running_loop()
        try:
            event = await loop.run_in_executor(
                None,
                lambda: stripe.Webhook.construct_event(
                    payload, sig_header, settings.STRIPE_CONNECT_WEBHOOK_SECRET
                ),
            )
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid Stripe signature")
        except Exception:
            raise HTTPException(status_code=400, detail="Malformed webhook payload")

        event_dict = event.to_dict()
        event_type: str = event_dict["type"]
        event_data: dict = event_dict["data"]["object"]

        print(f"event_type: {event_type}")
        print(f"event_data: {event_data}")

        match event_type:

            case "account.updated":
                stripe_account_id = event_data["id"]
                charges_enabled   = event_data["charges_enabled"]
                payouts_enabled   = event_data["payouts_enabled"]
                details_submitted = event_data["details_submitted"]

                result = await self.db.execute(
                    select(MechanicStripe).where(
                        MechanicStripe.stripe_account_id == stripe_account_id
                    )
                )
                mechanic_stripe = result.scalar_one_or_none()

                if mechanic_stripe:
                    mechanic_stripe.stripe_charges_enabled = charges_enabled
                    mechanic_stripe.stripe_payouts_enabled = payouts_enabled
                    mechanic_stripe.stripe_onboarded = (
                        details_submitted and charges_enabled and payouts_enabled
                    )
                    await self.db.commit()
                    print(f"✅ Updated MechanicStripe for account: {stripe_account_id}")
                else:
                    print(f"⚠️ No MechanicStripe found for account: {stripe_account_id}")

            case "capability.updated":
                stripe_account_id = event_data["account"]
                capability_id     = event_data["id"]      # "card_payments" or "transfers"
                status            = event_data["status"]  # "active" | "inactive"

                print(f"capability: {capability_id} → {status}")

                result = await self.db.execute(
                    select(MechanicStripe).where(
                        MechanicStripe.stripe_account_id == stripe_account_id
                    )
                )
                mechanic_stripe = result.scalar_one_or_none()

                if mechanic_stripe:
                    # Re-fetch the full account from Stripe to get the latest state
                    loop = asyncio.get_running_loop()
                    account = await loop.run_in_executor(
                        None,
                        lambda: stripe.Account.retrieve(stripe_account_id),
                    )
                    mechanic_stripe.stripe_charges_enabled = account.charges_enabled
                    mechanic_stripe.stripe_payouts_enabled = account.payouts_enabled
                    mechanic_stripe.stripe_onboarded = (
                        account.details_submitted
                        and account.charges_enabled
                        and account.payouts_enabled
                    )
                    await self.db.commit()
                    print(f"✅ Updated MechanicStripe for account: {stripe_account_id}")
                else:
                    print(f"⚠️ No MechanicStripe found for account: {stripe_account_id}")

            case _:
                print(f"unhandled event: {event_type}")

        return JSONResponse({"received": True, "handled": True})






    async def handle_webhook_payment(self, payload: bytes, sig_header: str | None) -> JSONResponse:

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

        event_dict = event.to_dict()
        event_type: str = event_dict["type"]
        event_data: dict = event_dict["data"]["object"]

        print(f"event_type: {event_type}")
        print(f"event_data: {event_data}")

        match event_type:

            case "payment_intent.succeeded":
                payment_intent_id = event_data["id"]
                charge_id         = event_data.get("latest_charge")

                result = await self.db.execute(
                    select(Payment).where(Payment.payment_intent_id == payment_intent_id)
                )
                payment = result.scalar_one_or_none()

                if payment:
                    charge = await loop.run_in_executor(
                        None,
                        lambda: stripe.Charge.retrieve(charge_id, expand=["transfer"]),
                    )

                    transfer    = charge.transfer         # the Transfer object
                    transfer_id = transfer.id if transfer else None
                    transfer_amount = transfer.amount if transfer else None

                    payment.status      = PaymentStatus.PAID
                    payment.transfer_id = transfer_id
                    await self.db.commit()
                    print(f"Payment succeeded: {payment_intent_id}")

     
                    mechanic_stripe_result = await self.db.execute(
                        select(MechanicStripe).where(
                            MechanicStripe.mechanic_id == payment.mechanic_id
                        )
                    )
                    mechanic_stripe = mechanic_stripe_result.scalar_one_or_none()

                    if mechanic_stripe:
                        mechanic_stripe.last_transfer_id     = transfer_id
                        mechanic_stripe.last_transfer_amount = transfer_amount
                        await self.db.commit()
                        print(f"Transfer saved: {transfer_id} — amount: {transfer_amount}")
                else:
                    print(f"No payment found for intent: {payment_intent_id}")


            case "payment_intent.payment_failed":
                payment_intent_id = event_data["id"]
                last_error        = event_data.get("last_payment_error") or {}
                failure_message   = last_error.get("message")
                failure_code      = last_error.get("code")

                result = await self.db.execute(
                    select(Payment).where(Payment.payment_intent_id == payment_intent_id)
                )
                payment = result.scalar_one_or_none()

                if payment:
                    payment.status          = PaymentStatus.FAILED
                    payment.failure_message = failure_message
                    payment.failure_code    = failure_code
                    await self.db.commit()
                    print(f"❌ Payment failed: {payment_intent_id} — {failure_code}: {failure_message}")
                else:
                    print(f"⚠️ No payment found for intent: {payment_intent_id}")

            case "charge.refunded":
                payment_intent_id = event_data.get("payment_intent")
                amount_refunded   = event_data.get("amount_refunded", 0)
                refund_reason     = event_data.get("refunds", {}).get("data", [{}])[0].get("reason")

                result = await self.db.execute(
                    select(Payment).where(Payment.payment_intent_id == payment_intent_id)
                )
                payment = result.scalar_one_or_none()

                if payment:
                    payment.status          = PaymentStatus.REFUNDED
                    payment.amount_refunded = amount_refunded
                    payment.refund_reason   = refund_reason
                    await self.db.commit()
                    print(f"↩️ Payment refunded: {payment_intent_id} — amount: {amount_refunded}")
                else:
                    print(f"⚠️ No payment found for intent: {payment_intent_id}")

            case _:
                print(f"unhandled event: {event_type}")

        return JSONResponse({"received": True, "handled": True})















