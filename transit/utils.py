from django.db import transaction
from .models import Seat, Booking
import requests
from django.conf import settings


def validate_seat_availability(seat_id, bus=None):
    """
    Validates if a seat is available for booking.
    """
    try:
        seat = Seat.objects.get(id=seat_id, bus=bus)
        if seat.is_booked:
            return False, seat
        return True, seat
    except Seat.DoesNotExist:
        return False, None


def generate_safaricom_token():
    """
    Generates an access token for the Safaricom Daraja API.
    """
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    auth = (settings.DARAJA_CONSUMER_KEY, settings.DARAJA_CONSUMER_SECRET)
    response = requests.get(url, auth=auth)
    response_data = response.json()
    return response_data.get("access_token")


def initiate_payment(seat, phone_number):
    """
    Initiates an STK Push payment request.
    """
    token = generate_safaricom_token()
    url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "BusinessShortCode": settings.DARAJA_SHORTCODE,
        "Password": settings.DARAJA_PASSKEY,
        "Timestamp": "20231219124536",  # Update dynamically in production
        "TransactionType": "CustomerPayBillOnline",
        "Amount": seat.price,
        "PartyA": phone_number,
        "PartyB": settings.DARAJA_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": settings.CALLBACK_URL,
        "AccountReference": f"Seat {seat.seat_label}",
        "TransactionDesc": "Bus Seat Booking"
    }
    response = requests.post(url, json=payload, headers=headers)
    response_data = response.json()
    if response_data.get("ResponseCode") == "0":
        return response_data.get("CheckoutRequestID")
    else:
        raise ValueError(f"Payment initiation failed: {response_data.get('errorMessage')}")


def create_booking(user, seat, phone_number):
    """
    Creates a booking, marks the seat as booked, and initiates payment in an atomic transaction.
    """
    with transaction.atomic():
        seat = Seat.objects.select_for_update().get(pk=seat.id)
        if seat.is_booked:
            raise ValueError(f"Seat {seat.seat_label} is already booked.")
        
        # Initiate payment
        checkout_request_id = initiate_payment(seat, phone_number)

        # Update seat status
        seat.is_booked = True
        seat.save()

        # Create a booking record
        booking = Booking.objects.create(
            user=user,
            seat=seat,
            transaction_id=checkout_request_id
        )

        return booking
