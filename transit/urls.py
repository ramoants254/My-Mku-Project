from django.urls import path, include
from . import views

urlpatterns=[
    path('', views.index,name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    # path('bookings/', views.bookings,name='bookings'),
    path('bus_booking/<int:bus_id>/', views.bus_booking,name='bus_booking'),
    path('route_details/<int:route_id>/', views.route_details,name='route_details'),
    # path('book/<int:seat_id>/', views.book_seat, name='book_seat'),
    # path('view_booking/<int:booking_id>/', views.view_booking, name='view_booking'),
    # path('add_route/',views.add_route,name='add_route'),
    path('bus/<int:bus_id>/', views.bus_detail, name='bus_detail'),
    # path('book/<int:seat_id>/', views.book_seat, name='book_seat'),
    # path('seat_selection/<int:bus_id>/', views.seat_selection, name='seat_selection'),
    # path('confirmation/<int:seat_id>/', views.confirmation, name='confirmation'),
    path('feedback/', views.feedback, name='feedback'),
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    path('check-payment-status/', views.check_payment_status, name='check_payment_status'),
    path('payment-status/', views.payment_status, name='payment_status'),





]