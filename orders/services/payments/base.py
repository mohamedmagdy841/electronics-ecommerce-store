from abc import ABC, abstractmethod

class BasePaymentGateway(ABC):
    @abstractmethod
    def send_payment(self, request, user, amount, order):
        """Initiate payment and return metadata (redirect url, transaction id, etc.)"""
        pass

    @abstractmethod
    def callback(self, request):
        """Handle callback/notification from payment provider"""
        pass
