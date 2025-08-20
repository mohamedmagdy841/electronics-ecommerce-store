import stripe
from django.conf import settings
from decimal import Decimal
from .base import BasePaymentGateway
import logging
logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeGateway(BasePaymentGateway):
    method = "stripe"
    provider_name = "Stripe"

    def send_payment(self, request, user, amount: Decimal, order):
        amount_cents = int(amount * 100)

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Order #{order.id}",
                    },
                    "unit_amount": amount_cents,
                },
                "quantity": 1,
            }],
            payment_intent_data={
                "metadata": {
                    "order_id": str(order.id),
                    "user_id": str(user.id),
                }
            },
            metadata={
                "order_id": str(order.id),
                "user_id": str(user.id),
            },
            success_url=settings.FRONTEND_URL + "/payment/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=settings.FRONTEND_URL + "/payment/cancel",
        )

        return {
            "transaction_id": session.id,
            "redirect_url": session.url,
            "status": "pending",
        }

    def callback(self, request):
        """Handle webhook events"""
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except (ValueError, stripe.error.SignatureVerificationError) as e:
            logger.error("Webhook signature verification failed: %s", e)
            return None
        
        logger.info("Received Stripe event: %s", event["type"])
        
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            order_id = session.get("metadata", {}).get("order_id")
            intent_id = session["payment_intent"]
            if not order_id:
                logger.error("Session missing order_id metadata")
                return None
            return {
                "order_id": order_id,
                "transaction_id": intent_id,
                "status": "success",
            }

        elif event["type"] == "payment_intent.succeeded":
            intent = event["data"]["object"]
            order_id = intent.get("metadata", {}).get("order_id")
            if not order_id:
                logger.error("PaymentIntent missing order_id metadata")
                return None
            return {
                "order_id": order_id,
                "transaction_id": intent["id"],
                "status": "success",
            }
            
        elif event["type"] == "payment_intent.payment_failed":
            intent = event["data"]["object"]
            order_id = intent.get("metadata", {}).get("order_id")
            if not order_id:
                logger.error("PaymentIntent missing order_id metadata")
                return None
            return {
                "order_id": order_id,
                "transaction_id": intent["id"],
                "status": "failed",
            }

        elif event["type"] == "charge.succeeded":
            charge = event["data"]["object"]
            try:
                intent = stripe.PaymentIntent.retrieve(charge["payment_intent"])
            except Exception as e:
                logger.error("Failed to retrieve PaymentIntent: %s", e)
                return None

            order_id = intent.get("metadata", {}).get("order_id")
            if not order_id:
                logger.error("Charge’s PaymentIntent missing order_id metadata")
                return None
            return {
                "order_id": order_id,
                "transaction_id": intent["id"],
                "status": "success",
            }

        return None
