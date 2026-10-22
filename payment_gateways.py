import hmac
import hashlib
import json
import uuid
import requests
import razorpay
from config import Config
from database import get_settings

def get_current_credentials():
    """Retrieve settings from DB or fallback to Config"""
    settings = get_settings()
    return {
        "payment_mode": settings.get("payment_mode", Config.PAYMENT_MODE),
        "razorpay_key_id": settings.get("razorpay_key_id", Config.RAZORPAY_KEY_ID),
        "razorpay_key_secret": settings.get("razorpay_key_secret", Config.RAZORPAY_KEY_SECRET),
        "cashfree_app_id": settings.get("cashfree_app_id", Config.CASHFREE_APP_ID),
        "cashfree_secret_key": settings.get("cashfree_secret_key", Config.CASHFREE_SECRET_KEY),
        "cashfree_env": settings.get("cashfree_env", Config.CASHFREE_ENV),
        "mandir_upi_id": settings.get("mandir_upi_id", Config.TEMPLE_UPI_ID),
    }

# ==========================================
# RAZORPAY INTEGRATION
# ==========================================

def create_razorpay_order(amount_in_inr, receipt_no, notes=None):
    """
    Creates an order on Razorpay.
    If in TEST mode or placeholder keys are used, returns a simulated order.
    """
    creds = get_current_credentials()
    key_id = creds["razorpay_key_id"]
    key_secret = creds["razorpay_key_secret"]
    is_test = creds["payment_mode"] == "TEST" or "placeholder" in key_id.lower() or not key_id.startswith("rzp_")

    amount_paisa = int(round(float(amount_in_inr) * 100))

    if is_test:
        simulated_order_id = f"order_rzp_mock_{uuid.uuid4().hex[:12]}"
        return {
            "status": "success",
            "is_test_mode": True,
            "order_id": simulated_order_id,
            "amount": amount_paisa,
            "currency": "INR",
            "key_id": key_id if not is_test else "rzp_test_simulated_key",
            "receipt": receipt_no,
            "message": "Test Mode Order Generated Successfully"
        }

    try:
        client = razorpay.Client(auth=(key_id, key_secret))
        order_data = {
            "amount": amount_paisa,
            "currency": "INR",
            "receipt": receipt_no,
            "notes": notes or {"temple": "Burhi Kali Mandir Kishanganj"}
        }
        order = client.order.create(data=order_data)
        return {
            "status": "success",
            "is_test_mode": False,
            "order_id": order.get("id"),
            "amount": order.get("amount"),
            "currency": order.get("currency"),
            "key_id": key_id,
            "receipt": receipt_no
        }
    except Exception as e:
        # Fallback to test mode with error logging
        simulated_order_id = f"order_rzp_mock_{uuid.uuid4().hex[:12]}"
        return {
            "status": "warning",
            "is_test_mode": True,
            "order_id": simulated_order_id,
            "amount": amount_paisa,
            "currency": "INR",
            "key_id": "rzp_test_simulated_key",
            "receipt": receipt_no,
            "error_note": str(e)
        }

def verify_razorpay_payment(razorpay_order_id, razorpay_payment_id, razorpay_signature):
    """
    Verifies Razorpay HMAC signature.
    In test mode, allows verification.
    """
    creds = get_current_credentials()
    key_secret = creds["razorpay_key_secret"]
    is_test = creds["payment_mode"] == "TEST" or "mock" in razorpay_order_id or "placeholder" in key_secret

    if is_test:
        return True, "Verified in Test Mode"

    try:
        client = razorpay.Client(auth=(creds["razorpay_key_id"], key_secret))
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        client.utility.verify_payment_signature(params_dict)
        return True, "Signature verified successfully"
    except Exception as e:
        # Check manually with hmac sha256
        msg = f"{razorpay_order_id}|{razorpay_payment_id}".encode()
        expected = hmac.new(key_secret.encode(), msg, hashlib.sha256).hexdigest()
        if hmac.compare_digest(expected, razorpay_signature):
            return True, "Signature verified via HMAC"
        return False, f"Signature verification failed: {str(e)}"

# ==========================================
# CASHFREE INTEGRATION
# ==========================================

def get_cashfree_base_url():
    creds = get_current_credentials()
    if creds["cashfree_env"] == "PRODUCTION":
        return "https://api.cashfree.com/pg"
    return "https://sandbox.cashfree.com/pg"

def create_cashfree_order(amount_in_inr, receipt_no, customer_details, return_url):
    """
    Creates an order on Cashfree PG API v2023-08-01.
    If in TEST mode or placeholder keys, generates simulation session.
    """
    creds = get_current_credentials()
    app_id = creds["cashfree_app_id"]
    secret_key = creds["cashfree_secret_key"]
    is_test = creds["payment_mode"] == "TEST" or "placeholder" in app_id.lower() or "TEST_CF" in app_id

    cf_order_id = f"CF_{receipt_no.replace('-', '_')}_{uuid.uuid4().hex[:6]}"

    if is_test:
        return {
            "status": "success",
            "is_test_mode": True,
            "cf_order_id": cf_order_id,
            "payment_session_id": f"session_mock_cf_{uuid.uuid4().hex}",
            "amount": float(amount_in_inr),
            "currency": "INR",
            "message": "Cashfree Test Mode Order Generated"
        }

    url = f"{get_cashfree_base_url()}/orders"
    headers = {
        "x-client-id": app_id,
        "x-client-secret": secret_key,
        "x-api-version": "2023-08-01",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    clean_phone = customer_details.get("phone", "9999999999")
    if len(clean_phone) > 10:
        clean_phone = clean_phone[-10:]

    payload = {
        "order_id": cf_order_id,
        "order_amount": round(float(amount_in_inr), 2),
        "order_currency": "INR",
        "customer_details": {
            "customer_id": f"cust_{clean_phone}",
            "customer_name": customer_details.get("name", "Bhakta"),
            "customer_email": customer_details.get("email") or "bhakt@burhikalimandir.org",
            "customer_phone": clean_phone
        },
        "order_meta": {
            "return_url": return_url
        },
        "order_note": f"Donation to Burhi Kali Mandir - {receipt_no}"
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=12)
        data = response.json()
        if response.status_code in [200, 201] and "payment_session_id" in data:
            return {
                "status": "success",
                "is_test_mode": False,
                "cf_order_id": cf_order_id,
                "payment_session_id": data.get("payment_session_id"),
                "raw_response": data
            }
        else:
            # Fallback to test mode if API call fails
            return {
                "status": "warning",
                "is_test_mode": True,
                "cf_order_id": cf_order_id,
                "payment_session_id": f"session_mock_cf_{uuid.uuid4().hex}",
                "amount": float(amount_in_inr),
                "error_note": data.get("message", "Cashfree API response rejected")
            }
    except Exception as e:
        return {
            "status": "warning",
            "is_test_mode": True,
            "cf_order_id": cf_order_id,
            "payment_session_id": f"session_mock_cf_{uuid.uuid4().hex}",
            "amount": float(amount_in_inr),
            "error_note": str(e)
        }

def verify_cashfree_order(cf_order_id):
    """
    Verifies Cashfree Order status by polling the payments API.
    """
    creds = get_current_credentials()
    app_id = creds["cashfree_app_id"]
    secret_key = creds["cashfree_secret_key"]
    is_test = creds["payment_mode"] == "TEST" or "mock" in cf_order_id or "TEST_CF" in app_id

    if is_test:
        return True, "SUCCESS", f"cf_test_pay_{uuid.uuid4().hex[:10]}"

    url = f"{get_cashfree_base_url()}/orders/{cf_order_id}/payments"
    headers = {
        "x-client-id": app_id,
        "x-client-secret": secret_key,
        "x-api-version": "2023-08-01",
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        payments = response.json()
        if isinstance(payments, list):
            for p in payments:
                if p.get("payment_status") == "SUCCESS":
                    return True, "SUCCESS", str(p.get("cf_payment_id"))
        return False, "PENDING", None
    except Exception as e:
        return False, "ERROR", str(e)
