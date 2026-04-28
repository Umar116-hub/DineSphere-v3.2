from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    This is a shared base model for both customers and restaurant owners. It includes common fields such as email, role, and profile image. The role field distinguishes between customers and owners, allowing for role-based access control and functionality within the application
    """
    email = models.EmailField(unique=True)

    ROLE_CHOICES = [
        ('CUSTOMER', 'Customer'),
        ('OWNER', 'Owner'),
        ('STAFF', 'Staff')
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    image = models.ImageField(upload_to='UsersHandling/media/images/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)



    class Gender(models.TextChoices):
        MALE = 'M', 'Male'
        FEMALE = 'F', 'Female'
        OTHER = 'O', 'Other'

    gender = models.CharField(
        max_length=1,
        choices=Gender.choices,
        blank=True,
        null=True
    )


class CustomerProfile(models.Model):
    """
    This model stores additional information specific to customer users. It includes fields such as tier, total spent, and total reservations. The tier field categorizes customers based on their spending and reservation history, which can be used to offer personalized rewards, promotions or even additional features.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    TIER_CHOICES = [
        ('GREEN', 'Green'),
        ('BLUE', 'Blue'),
        ('PURPLE', 'Purple'),
    ]
    tier = models.CharField(max_length=10, choices=TIER_CHOICES, default='Purple')

    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_reservations = models.IntegerField(default=0)

    # def __str__(self):
        # return f"Username: {self.user.mo}"


class RestaurantStaff(models.Model):
    """This model represents the staff members of a restaurant. The role field specifies whether the staff member is an owner or regular staff, which can be used to manage permissions and access levels within the restaurant's management system.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    restaurant = models.ForeignKey('Restaurants.Restaurant', on_delete=models.CASCADE, blank=True, null=True)

    ROLE_CHOICES = [
        ('OWNER', 'Owner'),
        ('STAFF', 'Staff'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    is_premium = models.BooleanField(default=False)