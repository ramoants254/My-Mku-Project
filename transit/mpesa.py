import requests
from datetime import datetime
import base64
from django.conf import settings
import logging
from django.urls import reverse

logger = logging.getLogger(__name__)

def generate_access_token():
    """Fetch Mpesa access token."""
    try:
        auth_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        response = requests.get(
            auth_url, 
            auth=(settings.MPESA_CONFIG['CONSUMER_KEY'], settings.MPESA_CONFIG['CONSUMER_SECRET'])
        )
        response.raise_for_status()
        return response.json().get('access_token')
    except Exception as e:
        logger.error(f"Error generating access token: {str(e)}")
        raise


def generate_password():
    """Generate Mpesa password using shortcode, passkey, and timestamp."""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    data_to_encode = f"{settings.MPESA_CONFIG['BUSINESS_SHORTCODE']}{settings.MPESA_CONFIG['PASSKEY']}{timestamp}"
    encoded_password = base64.b64encode(data_to_encode.encode()).decode()
    return encoded_password, timestamp


def initiate_mpesa_payment(phone_number, amount, account_reference, callback_url):
    """
    Initiates an Mpesa STK push request.
    """
    try:
        access_token = generate_access_token()
        password, timestamp = generate_password()

        # Format phone number
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        elif not phone_number.startswith('254'):
            phone_number = '254' + phone_number

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "BusinessShortCode": settings.MPESA_CONFIG['BUSINESS_SHORTCODE'],
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": settings.MPESA_CONFIG['TRANSACTION_TYPE'],
            "Amount": int(amount),
            "PartyA": int(phone_number),
            "PartyB": settings.MPESA_CONFIG['BUSINESS_SHORTCODE'],
            "PhoneNumber": int(phone_number),
            "CallBackURL": f"{settings.MPESA_CALLBACK_BASE_URL}{settings.MPESA_CALLBACK_ENDPOINT}",
            "AccountReference": str(account_reference),
            "TransactionDesc": "Bus Seat Booking Payment"
        }

        logger.info(f"Initiating M-Pesa payment with payload: {payload}")

        response = requests.post(
            f"{settings.MPESA_CONFIG['SANDBOX_URL']}/mpesa/stkpush/v1/processrequest",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        logger.info(f"M-Pesa API Response: {response.text}")
        
        if response.status_code != 200:
            logger.error(f"M-Pesa API Error: {response.status_code} - {response.text}")
            return {
                "ResponseCode": "1",
                "ResponseDescription": f"Payment request failed: {response.text}"
            }

        return response.json()

    except Exception as e:
        logger.error(f"Error in initiate_mpesa_payment: {str(e)}")
        return {
            "ResponseCode": "1",
            "ResponseDescription": f"An error occurred: {str(e)}"
        }



