from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Route, Bus, Seat, Feedback, Booking, Payment
from .utils import validate_seat_availability, create_booking, initiate_payment, generate_safaricom_token
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
import requests
import os
import base64
from datetime import datetime, timedelta
from django.conf import settings
from django.urls import reverse
import json
from django.http import JsonResponse 
from .mpesa import initiate_mpesa_payment
from .forms import BusBookingForm
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .mpesa_callbacks import MpesaCallback
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

# User Registration View
def register(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if not all([first_name, last_name, username, email, password, confirm_password]):
            messages.error(request, 'All fields are required.')
        elif password != confirm_password:
            messages.error(request, 'Passwords do not match.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
        else:
            User.objects.create_user(
                username=username, email=email, password=password,
                first_name=first_name, last_name=last_name
            )
            messages.success(request, 'Registration successful! Please log in.')
            return redirect('login')

        return redirect('register')

    return render(request, 'register.html')


# User Login View
def login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)
        if user:
            auth_login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Invalid username or password.')
        return redirect('login')

    return render(request, 'login.html')


# User Logout View
def logout(request):
    auth_logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('login')


# Home Page View (Requires Login)
def index(request):
    """Public landing page view"""
    return render(request, 'index.html')


# Dashboard View
@login_required
def dashboard(request):
    routes = Route.objects.prefetch_related('buses').all()
    return render(request, 'dashboard.html', {'routes': routes})


# Route Details View
@login_required
def route_details(request, route_id):
    route = get_object_or_404(Route, id=route_id)
    buses = route.buses.all()
    return render(request, 'route_details.html', {'route': route, 'buses': buses})


# # Bus Details View
# @login_required
# def bus_detail(request, bus_id):
#     bus = get_object_or_404(Bus, id=bus_id)
#     seats = bus.seats.all()
#     return render(request, 'bus_detail.html', {
#         'bus': bus,
#         'seats': seats,
#         'departure_time': bus.departure_time.strftime('%I:%M %p'),
#         'date': bus.date.strftime('%B %d, %Y'),
#     })

@login_required
def bus_detail(request, bus_id):
    bus = get_object_or_404(Bus.objects.select_related('route'), id=bus_id)
    seats = Seat.objects.filter(bus=bus).order_by('seat_label')
    form = BusBookingForm()
    
    context = {
        'bus': bus,
        'seats': seats,
        'form': form,
    }
    return render(request, 'bus_booking.html', context)



# Feedback View
@login_required
def feedback(request):
    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        rating = request.POST.get('rating', '')

        if not message:
            messages.error(request, 'Feedback cannot be empty.')
        elif not rating.isdigit() or not (1 <= int(rating) <= 5):
            messages.error(request, 'Invalid rating. Please select a number between 1 and 5.')
        else:
            Feedback.objects.create(user=request.user, message=message, rating=int(rating))
            messages.success(request, 'Thank you for your feedback!')
            return redirect('feedback')

    user_feedback = Feedback.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'feedback.html', {'user_feedback': user_feedback})



@csrf_exempt
@require_http_methods(["POST"])
def mpesa_callback(request):
    try:
        logger.info(f"Received callback request: {request.body.decode('utf-8')}")
        
        callback_data = json.loads(request.body.decode('utf-8'))
        logger.info(f"M-Pesa callback received: {callback_data}")
        
        # Process the callback
        callback_handler = MpesaCallback(callback_data)
        success = callback_handler.process_payment()
        
        if success:
            logger.info("Payment processed successfully")
            response_data = {
                "ResultCode": 0,
                "ResultDesc": "Callback processed successfully"
            }
        else:
            logger.warning("Payment processing failed")
            response_data = {
                "ResultCode": 1,
                "ResultDesc": "Callback processing failed"
            }
        
        logger.info(f"Sending response: {response_data}")
        return JsonResponse(response_data)
    
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in callback: {str(e)}")
        return JsonResponse({
            "ResultCode": 1,
            "ResultDesc": "Invalid JSON payload"
        }, status=400)
    
    except Exception as e:
        logger.error(f"Error processing callback: {str(e)}", exc_info=True)
        return JsonResponse({
            "ResultCode": 1,
            "ResultDesc": "Internal server error"
        }, status=500)





@login_required
def check_payment_status(request):
    """Check the status of a pending payment"""
    booking_data = request.session.get('pending_booking')
    if not booking_data:
        return JsonResponse({'status': 'no_booking'})

    try:
        # Check if there's a successful payment for this booking
        payment = Payment.objects.filter(
            user=request.user,  # Add user check
            transaction_id__isnull=False,
            status='SUCCESS',
            amount=booking_data['amount']
        ).order_by('-created_at').first()  # Get most recent payment

        if payment:
            # Check if booking exists for this payment
            booking = Booking.objects.filter(
                payment=payment,
                seat_id=booking_data['seat_id']
            ).exists()

            if booking:
                # Clear the pending booking from session
                del request.session['pending_booking']
                return JsonResponse({'status': 'success'})
            
        # Check if payment failed
        if payment and payment.status == 'FAILED':
            del request.session['pending_booking']
            return JsonResponse({
                'status': 'failed',
                'message': 'Payment failed. Please try again.'
            })
        
        # Add timeout check
        merchant_request_id = booking_data.get('merchant_request_id')
        if merchant_request_id:
            from django.utils import timezone
            from datetime import timedelta
            
            # If it's been more than 2 minutes since payment initiation
            if 'payment_initiated_at' in booking_data:
                initiated_at = datetime.fromisoformat(booking_data['payment_initiated_at'])
                if timezone.now() - initiated_at > timedelta(minutes=2):
                    del request.session['pending_booking']
                    return JsonResponse({
                        'status': 'timeout',
                        'message': 'Payment request timed out. Please try again.'
                    })
        
        return JsonResponse({'status': 'pending'})

    except Exception as e:
        logger.error(f"Error checking payment status: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@login_required
def bus_booking(request, bus_id):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        seat_id = request.POST.get('seat_id')
        
        logger.info(f"Received booking request for bus {bus_id}, seat {seat_id}, phone {phone_number}")
        
        if not seat_id or not phone_number:
            return JsonResponse({
                'status': 'error',
                'message': "Both seat and phone number are required."
            })

        try:
            seat = get_object_or_404(Seat, id=seat_id, bus_id=bus_id)
            
            if seat.is_booked:
                return JsonResponse({
                    'status': 'error',
                    'message': "Sorry, this seat has already been booked."
                })

            fare = seat.bus.route.fare
            
            # Create pending payment first
            payment = Payment.objects.create(
                user=request.user,
                amount=fare,
                status='PENDING'
            )
            
            # Format callback URL
            callback_url = f"{settings.MPESA_CALLBACK_BASE_URL}{settings.MPESA_CALLBACK_ENDPOINT}"
            logger.info(f"Using callback URL: {callback_url}")

            # Initiate M-Pesa payment
            payment_response = initiate_mpesa_payment(
                phone_number=phone_number,
                amount=float(fare),
                account_reference=f"Bus-{bus_id}-Seat-{seat_id}-Payment-{payment.id}",
                callback_url=callback_url
            )

            logger.info(f"M-Pesa Response: {payment_response}")

            if payment_response.get('ResponseCode') == '0':
                # Store booking attempt in session
                request.session['pending_booking'] = {
                    'bus_id': bus_id,
                    'seat_id': seat_id,
                    'phone_number': phone_number,
                    'amount': str(fare),
                    'payment_id': payment.id,
                    'merchant_request_id': payment_response.get('MerchantRequestID'),
                    'payment_initiated_at': timezone.now().isoformat()
                }
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Payment request sent. Please complete the payment on your phone.',
                    'redirect_url': reverse('payment_status')
                })
            else:
                # Mark payment as failed
                payment.status = 'FAILED'
                payment.save()
                
                error_message = payment_response.get('ResponseDescription', 'Unknown error')
                logger.error(f"Payment initiation failed: {error_message}")
                return JsonResponse({
                    'status': 'error',
                    'message': f"Failed to initiate payment: {error_message}"
                })

        except Exception as e:
            logger.error(f"Booking error: {str(e)}", exc_info=True)
            return JsonResponse({
                'status': 'error',
                'message': f"An error occurred: {str(e)}"
            })

    return JsonResponse({
        'status': 'error',
        'message': "Invalid request method."
    })

@login_required
def payment_status(request):
    """View to check payment status and show waiting page"""
    booking_data = request.session.get('pending_booking')
    if not booking_data:
        messages.error(request, "No pending booking found.")
        return redirect('dashboard')

    try:
        # Check if there's a successful payment
        payment = Payment.objects.filter(
            user=request.user,
            transaction_id__isnull=False,
            status='SUCCESS',
            amount=booking_data['amount']
        ).order_by('-created_at').first()

        if payment:
            # Check if booking exists
            booking = Booking.objects.filter(
                payment=payment,
                seat_id=booking_data['seat_id']
            ).exists()

            if booking:
                del request.session['pending_booking']
                messages.success(request, "Payment successful! Your seat has been booked.")
                return redirect('dashboard')

        # Check for timeout
        initiated_at = datetime.fromisoformat(booking_data['payment_initiated_at'])
        if timezone.is_naive(initiated_at):
            initiated_at = timezone.make_aware(initiated_at)
            
        if timezone.now() - initiated_at > timedelta(minutes=2):
            del request.session['pending_booking']
            messages.error(request, "Payment request timed out. Please try again.")
            return redirect('bus_detail', bus_id=booking_data['bus_id'])

        # If still pending, show the waiting page
        context = {
            'booking_data': booking_data,
            'refresh_interval': 5,  # Refresh every 5 seconds
        }
        return render(request, 'payment_status.html', context)

    except Exception as e:
        logger.error(f"Error checking payment status: {str(e)}", exc_info=True)
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('dashboard')