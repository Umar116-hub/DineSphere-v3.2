from django.db import models
from django.conf import settings

# Create your models here.


# -------------------------------
# Table Sizes (capacity + price factor)
# -------------------------------
class TableSize(models.Model):
    """
    Represents a table size with capacity and price factor.
    """
    capacity = models.PositiveIntegerField()
    size = models.CharField(max_length=20, blank=True, null=True)  # e.g., "Small", "Medium", "Large"
    price_factor = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    additional_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)  # Additional charges for whatever reasons

    def __str__(self):
        return f"{self.size} ({self.capacity} seats)"

    class Meta:
        unique_together = ('capacity', 'size')
        
    def calculate_price(self, base_price):
        return (base_price * self.price_factor) + self.additional_charges


# -------------------------------
# Seating Types
# -------------------------------
class SeatingType(models.Model):
    """
    Represents a type of seating, e.g., Indoor, Outdoor, VIP.
    """
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


# -------------------------------
# Restaurant
# -------------------------------
class Restaurant(models.Model):
    """
    Represents a restaurant with tables and seating options.
    """
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='Restaurants/media/images/', blank=True, null=True)
    about_restaurant = models.TextField(blank=True, null=True)
    seating_types = models.ManyToManyField(SeatingType, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    fb_link = models.URLField(blank=True, null=True)
    website_link = models.URLField(blank=True, null=True)
    has_top_offers = models.BooleanField(default=False)

    default_opening_hour = models.TimeField(default="18:00")  # 6 PM
    default_closing_hour = models.TimeField(default="01:00")  # 1 AM
    slot_duration_minutes = models.PositiveIntegerField(default=60)
    allow_advance_booking_days = models.PositiveIntegerField(default=60)
    cool_down = models.PositiveIntegerField(default=30)

    city = models.CharField(max_length=50)
    address = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_approved = models.BooleanField(default=False)

    @property
    def opening_hour(self):
        return self.default_opening_hour

    @property
    def closing_hour(self):
        return self.default_closing_hour

    def __str__(self):
        return self.name


# -------------------------------
# Tables
# -------------------------------
class Table(models.Model):
    """
    Represents a table in a restaurant. Tables can be combined dynamically to accommodate larger parties.
    """
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='tables')
    name = models.CharField(max_length=50)
    table_size = models.ForeignKey(TableSize, on_delete=models.PROTECT, related_name='tables')
    seating_type = models.ForeignKey(SeatingType, on_delete=models.SET_NULL, null=True, blank=True, default=None)
    is_available = models.BooleanField(default=True)
    is_combinable = models.BooleanField(default=True)  # Allows dynamic merging
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)  # Base price per table

    class Meta:
        unique_together = ('restaurant', 'name')

    @property
    def capacity(self):
        return self.table_size.capacity if self.table_size else None

    @property
    def size(self):
        return self.table_size.size if self.table_size else None

    def calculate_price(self):
        if self.table_size:
            return self.table_size.calculate_price(self.base_price)
        return self.base_price

    def __str__(self):
        return f"{self.restaurant.name} - Table {self.name} ({self.capacity} seats, {self.size})"




class SpecialDay(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    date = models.DateField()
    name = models.CharField(max_length=100, blank=True, null=True)
    closed_full_day = models.BooleanField(default=False)
    adjusted_opening_hour = models.IntegerField(null=True, blank=True)
    adjusted_closing_hour = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.restaurant.name} - {self.date}"


class FavouriteRestaurant(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favourites'
    )
    restaurant = models.ForeignKey(
        'Restaurant',
        on_delete=models.CASCADE,
        related_name='fans'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'restaurant'],
                name='unique_user_restaurant'
            )
        ]

    def __str__(self):
        return f"{self.user} → {self.restaurant}"


class Testimonials(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    text = models.TextField(blank=True, default="Amazing food and cozy atmosphere! The staff were friendly and attentive. Highly recommend for a great dining experience.")
    creator_name = models.CharField(blank=True, default="Anonymous")

    def __str__(self):
        return f"{self.creator_name} says: {self.text[:40]} ..."


class ReviewSummary(models.Model):
    restaurant = models.OneToOneField(
        Restaurant,
        related_name="review_summary",
        on_delete=models.CASCADE
    )

    five_star = models.PositiveIntegerField(default=0)
    four_star = models.PositiveIntegerField(default=0)
    three_star = models.PositiveIntegerField(default=0)
    two_star = models.PositiveIntegerField(default=0)
    one_star = models.PositiveIntegerField(default=0)
    points = models.PositiveIntegerField(default=0)

    def total_reviews(self):
        return (
            self.five_star +
            self.four_star +
            self.three_star +
            self.two_star +
            self.one_star
        )

    def average_rating(self):
        total = self.total_reviews()
        if total == 0:
            return 0.0

        score = (
            self.five_star * 5 +
            self.four_star * 4 +
            self.three_star * 3 +
            self.two_star * 2 +
            self.one_star * 1
        )

        return round(score / total, 1)
    
    @property
    def avg_rat(self):
        return self.average_rating()
    
    def __str__(self):
        return f"{self.average_rating()} ratings of {self.restaurant.name}"



class Review(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    on_display = models.BooleanField(default=False)

    def add_to_display(self):
        self.on_display = True
        self.save()
    
    def hide_from_display(self):
        self.on_display = False
        self.save()

    def __str__(self):
        return f"{self.user} rated {self.restaurant.name} - {self.rating} stars"