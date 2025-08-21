import requests, time, uuid, logging
from requests.auth import HTTPBasicAuth
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

TOKEN_KEY, EXP_KEY = "paypal_token", "paypal_token_exp"

def get_access_token() -> str:
    cached = cache.get(TOKEN_KEY)
    exp = cache.get(EXP_KEY)
    now = int(time.time())
    if cached and exp and now < exp - 60:
        return cached

    url = f"{settings.PAYPAL_API_BASE}/v1/oauth2/token"
    resp = requests.post(
        url,
        data={"grant_type": "client_credentials"},
        auth=HTTPBasicAuth(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
        headers={"Accept":"application/json","Accept-Language":"en_US"},
    )
    if resp.status_code != 200:
        raise RuntimeError(f"PayPal OAuth failed {resp.status_code}: {resp.text}")
    data = resp.json()
    token = data["access_token"]
    expires = int(data["expires_in"])
    cache.set(TOKEN_KEY, token, expires)
    cache.set(EXP_KEY, now+expires, expires)
    return token


def create_order(amount: str, currency: str, return_url: str, cancel_url: str, custom_id: str):
    url = f"{settings.PAYPAL_API_BASE}/v2/checkout/orders"
    token = get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "PayPal-Request-Id": str(uuid.uuid4()),  # idempotency
        "Prefer": "return=representation",
    }
    body = {
        "intent": "CAPTURE",
        "application_context": {
            "return_url": return_url,
            "cancel_url": cancel_url,
            "user_action": "PAY_NOW"
        },
        "purchase_units": [
            {
                "amount": {"currency_code": currency, "value": amount},
                "custom_id": str(custom_id)
            }
        ]
    }
    resp = requests.post(url, json=body, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    order_id = data["id"]
    approve = next((l["href"] for l in data["links"] if l["rel"] in ("approve","payer-action")), None)
    return order_id, approve


def capture_order(order_id: str):
    url = f"{settings.PAYPAL_API_BASE}/v2/checkout/orders/{order_id}/capture"
    token = get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "PayPal-Request-Id": str(uuid.uuid4()),
    }
    resp = requests.post(url, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    status = data.get("status")
    pu = data.get("purchase_units",[{}])[0]
    custom_id = pu.get("custom_id")
    captures = pu.get("payments",{}).get("captures",[])
    custom_id = captures[0]["custom_id"]
    capture_id = captures[0]["id"] if captures else order_id
    return {"status":status,"custom_id":custom_id,"capture_id":capture_id}
