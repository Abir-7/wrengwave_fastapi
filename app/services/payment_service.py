import asyncio
import stripe
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_payment_intent(self, amount: int, currency: str = "usd") -> stripe.PaymentIntent:
        if not isinstance(amount, int) or amount <= 0:
            raise ValueError(f"Amount must be a positive integer, got: {amount}")

        loop = asyncio.get_event_loop()

        try:
            intent: stripe.PaymentIntent = await loop.run_in_executor(
                None,
                lambda: stripe.PaymentIntent.create(
                    amount=amount,
                    currency=currency,
                    payment_method_types=["card"],
                ),
            )
            return intent
        except stripe.error.CardError as e:
            raise stripe.error.CardError(e.user_message, e.param, e.code, http_status=e.http_status) from e
        except stripe.error.InvalidRequestError as e:
            raise stripe.error.InvalidRequestError(e.user_message, e.param, http_status=e.http_status) from e
        except stripe.error.StripeError as e:
            raise stripe.error.StripeError(f"Stripe error: {e.user_message}") from e