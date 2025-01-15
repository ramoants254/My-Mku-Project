from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from django.contrib.auth.models import User

# Validator for future dates
def validate_future_date(value):
    if value < now().date():
        raise ValidationError("The date cannot be in the past.")

# Route Model
class Route(models.Model):
    start_point = models.CharField(max_length=100)
    end_point = models.CharField(max_length=100)
    fare = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Route'
        verbose_name_plural = 'Routes'

    def __str__(self):
        return f"{self.start_point} to {self.end_point} - {self.fare}"


# Bus Model
class Bus(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='buses')
    capacity = models.PositiveIntegerField(default=36)
    current_location = models.CharField(max_length=100)
    departure_time = models.TimeField()
    date = models.DateField(validators=[validate_future_date])

    class Meta:
        verbose_name = 'Bus'
        verbose_name_plural = 'Buses'

    def __str__(self):
        return f"Bus on {self.route} - Capacity: {self.capacity} - Departure: {self.departure_time}"


# Seat Model
class Seat(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='seats')
    seat_label = models.CharField(max_length=10)  # e.g., "A1", "B2"
    is_booked = models.BooleanField(default=False, editable=False)  # Indicates if the seat is booked

    class Meta:
        unique_together = ('bus', 'seat_label')
        verbose_name = 'Seat'
        verbose_name_plural = 'Seats'

    def __str__(self):
        return f"Seat {self.seat_label} ({'Booked' if self.is_booked else 'Available'}) on {self.bus}"


# Feedback Model
class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Feedback'
        verbose_name_plural = 'Feedbacks'

    def __str__(self):
        return f"Feedback by {self.user.username} - {self.rating}"


# Payment Transaction Model
class Payment(models.Model):
    TRANSACTION_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    status = models.CharField(max_length=10, choices=TRANSACTION_STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'

    def __str__(self):
        return f"Payment {self.transaction_id} - {self.status}"


# Booking Model
class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    payment = models.OneToOneField(Payment, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'

    def save(self, *args, **kwargs):
        with transaction.atomic():
            # Lock the seat for this transaction
            seat = Seat.objects.select_for_update().get(pk=self.seat.pk)
            if seat.is_booked:
                raise ValueError("Seat is already booked.")
            seat.is_booked = True
            seat.save()
            super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Free up the seat when booking is deleted
        self.seat.is_booked = False
        self.seat.save()
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Booking for {self.user.username} - Seat {self.seat.seat_label} on {self.seat.bus}"
