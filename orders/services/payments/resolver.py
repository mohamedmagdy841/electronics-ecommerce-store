from .paypal import PaypalGateway
from .cod import CashOnDeliveryGateway
from .stripe import StripeGateway

class PaymentGatewayResolver:
    GATEWAYS = {
        "cod": CashOnDeliveryGateway,
        "stripe": StripeGateway,
        "paypal": PaypalGateway,
    }

    @classmethod
    def resolve(cls, gateway_type: str):
        if gateway_type not in cls.GATEWAYS:
            raise ValueError(f"Unsupported gateway type: {gateway_type}")
        return cls.GATEWAYS[gateway_type]()
