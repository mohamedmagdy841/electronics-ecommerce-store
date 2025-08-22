from decimal import Decimal
from django.conf import settings
from .base import BasePaymentGateway
from .paypal_api import create_order, capture_order

class PaypalGateway(BasePaymentGateway):
    method = "paypal"
    provider_name = "PayPal"

    def send_payment(self, request, user, amount: Decimal, order):
        order_id, approve_url = create_order(
            amount=f"{amount:.2f}",
            currency=settings.PAYPAL_CURRENCY,
            return_url=settings.PAYMENT_RETURN_URL,
            cancel_url=settings.PAYMENT_CANCEL_URL,
            custom_id=str(order.id),
        )
        return {
            "order_id": order_id,
            "transaction_id": None,   
            "redirect_url": approve_url,  # FE must redirect user here
            "status": "pending",
        }

    def callback(self, request):
        # PayPal returns ?token=<ORDER_ID> to return_url
        order_id = None
        if hasattr(request,"data"):
            order_id = request.data.get("order_id") or request.data.get("orderID")
        if not order_id and hasattr(request,"query_params"):
            order_id = request.query_params.get("token")
        if not order_id:
            return None

        result = capture_order(order_id)
        if result["status"] == "COMPLETED":
            return {
                "order_id": result["gateway_order_id"],
                "transaction_id": result["capture_id"],
                "status": "success",
            }
        return {
            "order_id": result["gateway_order_id"],
            "transaction_id": result["capture_id"],
            "status": "failed",
        }
