from django.db import models
# from Reservations.models import Restaurant, Table
from UsersHandling.models import User

class Booking(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_FINISHED = 'finished'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_FINISHED, 'Finished'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    restaurant = models.ForeignKey('Restaurants.Restaurant', on_delete=models.CASCADE)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    tables = models.ManyToManyField('Restaurants.Table', related_name='bookings')
    booking_start_datetime = models.DateTimeField()
    booking_end_datetime = models.DateTimeField()

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)

    # Payment status only - no card data stored (PCI compliance)
    payment_status = models.CharField(max_length=20, default='pending')

    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    locked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.restaurant.name} - {self.booking_start_datetime} to {self.booking_end_datetime}"


    def cancel(self):
        if self.status == self.STATUS_PENDING:
            self.status = self.STATUS_CANCELLED
            self.save()
        else:
            raise ValueError("Cannot cancel a booking that is already finished or cancelled.")

    def mark_finished(self):
        if self.status == self.STATUS_PENDING:
            self.status = self.STATUS_FINISHED
            self.save()