from .base import BasePaymentGateway
from .paymob_api import create_invoice

class PaymobGateway(BasePaymentGateway):
    method = "paymob"
    provider_name = "Paymob"
    
    def send_payment(self, request, user, amount, order):
        order_id, payment_url = create_invoice(amount=amount*100)
        return {
            "order_id": order_id,
            "transaction_id": None,
            "redirect_url": payment_url,
            "status": "pending",
        }

    def callback(self, request):
        data = request.data
        success = data.get("success")
        order = data.get("order", {})
        order_id = order.get("id")
        transaction_id = data.get("id")

        status = "success" if success else "failed"

        return {
            "transaction_id": transaction_id,
            "order_id": order_id,
            "status": status,
        }
        
    def callback_query(self, query_params):
        transaction_id = str(query_params.get("id"))
        order_id = str(query_params.get("order"))
        success = query_params.get("success") == "true"
        status = "success" if success else "failed"

        return {
            "transaction_id": transaction_id,
            "order_id": order_id,
            "status": status,
        }
