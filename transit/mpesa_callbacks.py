import logging
from decimal import Decimal
from django.db import transaction
from .models import Payment, Booking, Seat, User
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
from datetime import datetime

logger = logging.getLogger(__name__)

class MpesaCallback:
    def __init__(self, callback_data):
        self.callback_data = callback_data
        self.result_code = self.callback_data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
        self.merchant_request_id = self.callback_data.get('Body', {}).get('stkCallback', {}).get('MerchantRequestID')
        logger.info(f"Initialized MpesaCallback with result_code: {self.result_code}")
        
    def get_callback_metadata(self):
        try:
            callback_items = self.callback_data.get('Body', {}).get('stkCallback', {}).get('CallbackMetadata', {}).get('Item', [])
            metadata = {}
            for item in callback_items:
                name = item.get('Name')
                value = item.get('Value')
                metadata[name] = value
            return metadata
        except Exception as e:
            logger.error(f"Error parsing callback metadata: {str(e)}")
            return None

    @transaction.atomic
    def process_payment(self):
        try:
            if self.result_code != 0:
                logger.error(f"Payment failed with result code: {self.result_code}")
                return False

            metadata = self.get_callback_metadata()
            if not metadata:
                logger.error("No callback metadata found")
                return False

            # Get booking reference
            booking_reference = self.callback_data.get('Body', {}).get('stkCallback', {}).get('AccountReference')
            if not booking_reference:
                logger.error("No booking reference found")
                return False

            try:
                # Parse the booking reference
                _, bus_id, _, seat_id, _, payment_id = booking_reference.split('-')
                
                # Get the existing payment
                payment = Payment.objects.select_for_update().get(id=payment_id)
                
                # Update payment with M-Pesa details
                payment.transaction_id = metadata.get('MpesaReceiptNumber')
                payment.status = 'SUCCESS'
                payment.save()

                # Create booking
                seat = Seat.objects.select_for_update().get(id=seat_id, bus_id=bus_id)
                if not seat.is_booked:
                    seat.is_booked = True
                    seat.save()
                    
                    Booking.objects.create(
                        user=payment.user,
                        seat=seat,
                        payment=payment
                    )
                    
                    logger.info(f"Successfully processed payment and created booking")
                    return True
                else:
                    logger.warning(f"Seat {seat_id} was already booked")
                    return False

            except Exception as e:
                logger.error(f"Error processing booking: {str(e)}", exc_info=True)
                return False

        except Exception as e:
            logger.error(f"Error in process_payment: {str(e)}", exc_info=True)
            return False 