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
    
    PAYMENT_STATUS_PENDING = 'pending'
    PAYMENT_STATUS_PAID = 'paid'
    PAYMENT_STATUS_FAILED = 'failed'
    PAYMENT_STATUS_REFUNDED = 'refunded'
    
    PAYMENT_CHOICES = [
        (PAYMENT_STATUS_PENDING, 'Pending'),
        (PAYMENT_STATUS_PAID, 'Paid'),
        (PAYMENT_STATUS_FAILED, 'Failed'),
        (PAYMENT_STATUS_REFUNDED, 'Refunded'),
    ]

    restaurant = models.ForeignKey('Restaurants.Restaurant', on_delete=models.CASCADE)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    tables = models.ManyToManyField('Restaurants.Table', related_name='bookings')
    booking_start_datetime = models.DateTimeField()
    booking_end_datetime = models.DateTimeField()

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)

    # Payment status only - no card data stored (PCI compliance)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default=PAYMENT_STATUS_PENDING)

    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    locked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def guest_count(self):
        """Calculates total seating capacity for the booking from reserved tables."""
        total = 0
        for table in self.tables.all():
            if table.capacity:
                total += table.capacity
        return total

    def __str__(self):
        return f"{self.restaurant.name} - {self.booking_start_datetime} to {self.booking_end_datetime}"


    def clean(self):
        from django.core.exceptions import ValidationError
        if self.customer and self.customer.role != 'CUSTOMER':
            raise ValidationError("Only customer accounts can make reservations.")

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