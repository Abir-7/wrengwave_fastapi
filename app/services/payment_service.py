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
        print("handle_webhook")
      
        if not sig_header:
            raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")
        print("handle_webhook2")
        loop = asyncio.get_running_loop()
        try:
            event = await loop.run_in_executor(
                None,
                lambda: stripe.Webhook.construct_event(
                    payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
                ),
            )
            print("handle_webhook3")
        except stripe.error.SignatureVerificationError:
            print("handle_err")
            raise HTTPException(status_code=400, detail="Invalid Stripe signature")
        except Exception:
            print("handle_err2")
            raise HTTPException(status_code=400, detail="Malformed webhook payload")

        # ✅ Convert Stripe object to plain dict first
        event_dict = event.to_dict()

        event_type: str          = event_dict["type"]

        print(event_type)

        event_obj:  dict         = event_dict["data"]["object"]
        connected_account_id: str | None = event_dict.get("account")  # acct_xxxx
        print(event_type)
        if event_type not in WEBHOOK_HANDLERS:
            return JSONResponse({"received": True, "handled": False})

        handler_map = {
            "account.updated":               self._on_account_updated,
            "application_fee.created":       self._on_application_fee_created,
            "charge.refunded":               self._on_charge_refunded,
            "payment_intent.succeeded":      self._on_payment_succeeded,
            "payment_intent.payment_failed": self._on_payment_failed,
            "transfer.created":              self._on_transfer_created,
        }

        handler = handler_map.get(event_type)
        # if handler:
        #     await handler(event_obj, connected_account_id)

        # return JSONResponse({"received": True, "handled": True})
    # ─────────────────────────────────────────────────────────────────────────
    # SHARED DB HELPERS
    # ─────────────────────────────────────────────────────────────────────────

    async def _get_payment(self, payment_intent_id: str) -> Payment | None:
        result = await self.db.execute(
            select(Payment).where(Payment.payment_intent_id == payment_intent_id)
        )
        return result.scalar_one_or_none()

    async def _get_mechanic_stripe(self, stripe_account_id: str) -> MechanicStripe | None:
        result = await self.db.execute(
            select(MechanicStripe).where(
                MechanicStripe.stripe_account_id == stripe_account_id
            )
        )
        return result.scalar_one_or_none()

    # ─────────────────────────────────────────────────────────────────────────
    # EVENT HANDLERS
    # ─────────────────────────────────────────────────────────────────────────

    async def _on_payment_succeeded(self, intent: dict, account_id: str | None) -> None:
        payment = await self._get_payment(intent["id"])
        if not payment:
            logger.warning(f"payment_intent.succeeded: not found {intent['id']}")
            return

        payment.status = PaymentStatus.PAID
        await self.db.commit()
        logger.info(f"Payment {intent['id']} → PAID")

    async def _on_payment_failed(self, intent: dict, account_id: str | None) -> None:
        payment = await self._get_payment(intent["id"])
        if not payment:
            logger.warning(f"payment_intent.payment_failed: not found {intent['id']}")
            return

        last_error      = intent.get("last_payment_error") or {}
        failure_message = last_error.get("message")
        failure_code    = last_error.get("code")

        payment.status          = PaymentStatus.FAILED
        payment.failure_message = failure_message
        payment.failure_code    = failure_code
        await self.db.commit()
        logger.info(f"Payment {intent['id']} → FAILED | {failure_code}: {failure_message}")

    async def _on_account_updated(self, account: dict, account_id: str | None) -> None:
        stripe_account_id = account.get("id")

        logger.info(
        f"account.updated payload → "
        f"id={stripe_account_id} | "
        f"details_submitted={account.get('details_submitted')} | "
        f"charges_enabled={account.get('charges_enabled')} | "
        f"payouts_enabled={account.get('payouts_enabled')}"
    )

        mechanic_stripe = await self._get_mechanic_stripe(stripe_account_id)
        if not mechanic_stripe:
            logger.warning(f"account.updated: no record found for {stripe_account_id}")
            return
        print(account)
        mechanic_stripe.stripe_onboarded       = account.get("details_submitted", False)
        mechanic_stripe.stripe_charges_enabled = account.get("charges_enabled", False)
        mechanic_stripe.stripe_payouts_enabled = account.get("payouts_enabled", False)
        await self.db.commit()
        logger.info(
            f"MechanicStripe {mechanic_stripe.mechanic_id} → "
            f"onboarded={mechanic_stripe.stripe_onboarded}"
        )

    async def _on_application_fee_created(self, fee: dict, account_id: str | None) -> None:
        logger.info(
            f"App fee → id={fee.get('id')} | "
            f"amount={fee.get('amount')} {fee.get('currency')} | "
            f"charge={fee.get('charge')} | account={account_id}"
        )

    async def _on_charge_refunded(self, charge: dict, account_id: str | None) -> None:
        payment_intent_id = charge.get("payment_intent")
        amount_refunded   = charge.get("amount_refunded", 0)
        refunds_data      = charge.get("refunds", {}).get("data", [])
        latest_refund     = refunds_data[0] if refunds_data else {}

        if not payment_intent_id:
            logger.warning("charge.refunded: no payment_intent_id on charge")
            return

        payment = await self._get_payment(payment_intent_id)
        if not payment:
            logger.warning(f"charge.refunded: payment not found {payment_intent_id}")
            return

        if charge.get("amount") == amount_refunded:
            payment.status = PaymentStatus.REFUNDED
        else:
            payment.status = PaymentStatus.PARTIALLY_REFUNDED

        payment.amount_refunded = amount_refunded
        payment.refund_reason   = latest_refund.get("reason")
        await self.db.commit()
        logger.info(f"Payment {payment_intent_id} → {payment.status} | {amount_refunded} cents")

    async def _on_transfer_created(self, transfer: dict, account_id: str | None) -> None:
        destination = transfer.get("destination")
        # payment_intent_id = transfer.get("source_transaction")
        # if payment_intent_id:
        #     payment = await self._get_payment(payment_intent_id)
        #     if payment:
        #         payment.status = PaymentStatus.PAID
        #         await self.db.commit()
        #         logger.info(f"Payment {payment_intent_id} → PAID via transfer {transfer.get('id')}")

        mechanic_stripe = await self._get_mechanic_stripe(destination)
        if not mechanic_stripe:
            logger.warning(f"transfer.created: no record found for {destination}")
            return

        mechanic_stripe.last_transfer_id     = transfer.get("id")
        mechanic_stripe.last_transfer_amount = transfer.get("amount")
        await self.db.commit()
        logger.info(
            f"Transfer → mechanic {mechanic_stripe.mechanic_id} | "
            f"{transfer.get('id')} | {transfer.get('amount')} {transfer.get('currency')}"
        )