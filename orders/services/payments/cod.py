import uuid
from .base import BasePaymentGateway

class CashOnDeliveryGateway(BasePaymentGateway):
    provider_name = None
    method = "cod"
    
    def send_payment(self, request, user, amount, order):
        return {
            "success": True,
            "transaction_id": str(uuid.uuid4()),
            "status": "pending",
        }

    def callback(self, request):
        return {"success": True, "status": "success"}
