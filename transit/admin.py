# from django.contrib import admin
# from .models import Route, Bus, Seat, Feedback, Booking

# #Register your models here.
# admin.site.register(Route)
# admin.site.register(Bus)
# admin.site.register(Seat)
# admin.site.register(Booking)
# admin.site.register(Feedback)

from django.contrib import admin
from .models import Route, Bus, Seat, Feedback, Booking

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('start_point', 'end_point', 'fare')

@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ('route', 'capacity', 'current_location', 'departure_time', 'date')
    list_filter = ('route', 'date')

@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ('bus', 'seat_label', 'is_booked')
    list_filter = ('bus', 'is_booked')
    readonly_fields = ('is_booked',)

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'seat', 'date')
    list_filter = ('date',)
