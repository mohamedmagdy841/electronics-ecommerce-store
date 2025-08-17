from .cod import CashOnDeliveryGateway


class PaymentGatewayResolver:
    GATEWAYS = {
        "cod": CashOnDeliveryGateway,
    }

    @classmethod
    def resolve(cls, gateway_type: str):
        if gateway_type not in cls.GATEWAYS:
            raise ValueError(f"Unsupported gateway type: {gateway_type}")
        return cls.GATEWAYS[gateway_type]()
