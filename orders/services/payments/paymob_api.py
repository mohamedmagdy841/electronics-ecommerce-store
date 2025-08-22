from django.conf import settings
import requests

def _get_access_token() -> str:
    API_KEY = settings.PAYMOB_API_KEY
    url = settings.PAYMOB_API_BASE + "/api/auth/tokens"
    headers = {
        "Content-Type": "application/json"
    }    
    resp = requests.post(
        url,
        headers=headers,
        json={
            "api_key": API_KEY
        }
    )
    resp.raise_for_status()
    data = resp.json()
    token = data["token"]
    return token

def create_invoice(amount):
    url = settings.PAYMOB_API_BASE + "/api/ecommerce/orders"
    token = _get_access_token()
    headers = {
        "Content-Type": "application/json",
    }
    body = {
        "auth_token": token,
        "api_source": "INVOICE",
        "amount_cents": str(amount),
        "currency": settings.PAYMOB_CURRENCY,
        "shipping_data": {
            "first_name": "Test",
            "last_name": "Account",
            "phone_number": "01010101010",
            "email": "test@account.com"
        },
        "integrations": settings.PAYMOB_INTEGRATIONS,
    }
    resp = requests.post(
        url,
        headers=headers,
        json=body
    )
    resp.raise_for_status()
    data = resp.json()
    order_id = data["id"]
    payment_url = data["url"]
    return order_id, payment_url
