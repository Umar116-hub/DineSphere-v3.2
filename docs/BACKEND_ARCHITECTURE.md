# DineSphere - Backend Architecture

## Request Flow Diagram

```
HTTP Request
    ↓
URL Router (urls.py)
    ↓
Middleware Stack
    - SessionMiddleware
    - AuthenticationMiddleware
    - CSRF Protection
    ↓
View Layer (views.py)
    ↓
Decorators
    - @login_required
    - @restrict_access
    ↓
Business Logic
    - Services (Services.py)
    - Utils (utils.py)
    ↓
Data Access Layer
    - Models (models.py)
    - ORM Queries
    ↓
Database (SQLite3)
    ↓
Response
    - HTML Template
    - JSON (AJAX)
    - Redirect
```

---

## App Structure

### 1. Core App (`/Core/`)
**Purpose:** Public-facing customer functionality

**Views:**
```python
# Core/views.py
home_page(request)          # Landing page with featured restaurants
    ↓
profile(request)            # User profile & booking history
    ↓
search(request)             # Restaurant search results
    ↓
aboutus(request)            # Static about page
    ↓
contactus(request)          # Static contact page
```

**Data Flow - Home Page:**
```python
def home_page(request):
    # 1. Query approved restaurants
    restaurants = Restaurant.objects.filter(is_approved=True)
    
    # 2. If authenticated, get user's favourites
    if request.user.is_authenticated:
        user_favs = FavouriteRestaurant.objects.filter(
            user=request.user
        ).values_list('restaurant_id', flat=True)
        
        # Annotate restaurants with is_favourite flag
        restaurants = restaurants.annotate(
            is_favourite=Case(
                When(id__in=user_favs, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        )
    
    # 3. Get reviews for ratings display
    reviews = Review.objects.all()
    
    # 4. Combine data for template
    combined = []
    for restaurant in restaurants:
        restaurant_reviews = reviews.filter(restaurant=restaurant)
        avg_rating = restaurant_reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        combined.append({
            'restaurant': restaurant,
            'avg_rating': avg_rating,
            'total_reviews': restaurant_reviews.count()
        })
    
    # 5. Render template
    return render(request, "Core/home.html", {
        "Restaurants": restaurants,
        "combined": combined,
        "user_image": user_image
    })
```

---

### 2. UsersHandling App (`/UsersHandling/`)
**Purpose:** Authentication and user management

**Views:**
```python
# UsersHandling/views.py
auth_view(request)          # Shows login/signup forms
    ↓
signup_user(request)        # Handles registration
    ↓
login_user(request)         # [FIXED] Now has rate limiting
    ↓
logout_user(request)        # Session cleanup
    ↓
update_profile(request)     # Profile edits
```

**Registration Flow:**
```
POST /uh/signup/
    ↓
Validate password strength [NEW]
    ↓
Create User record
    ↓
Create CustomerProfile record
    ↓
Auto-login user
    ↓
Redirect to home
```

**Authentication Decorator:**
```python
# Restaurants/decorators.py
def restrict_access(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Check if user has required role for restaurant
            staff = RestaurantStaff.objects.filter(
                user=request.user,
                restaurant_id=restaurant_id,
                role__in=allowed_roles
            ).first()
            
            if not staff:
                return HttpResponseForbidden("Access denied")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
```

---

### 3. Restaurants App (`/Restaurants/`)
**Purpose:** Restaurant management (owner/staff)

**Views Structure:**
```python
# Owner Dashboard & Analytics
analytics(request)          # Main dashboard with stats
switch_business(request)    # Change active restaurant

# Restaurant CRUD
register_restaurant(request)  # Create new restaurant
edit_restaurant(request, id)  # Update details
business_info(request)        # View/edit info

# Table Management
tables(request)             # List all tables
add_table(request)          # Create table
edit_table(request, id)     # Modify table
delete_table(request, id)   # Remove table

# Staff Management
staff_management(request)   # List staff
add_staff(request)          # Add employee
remove_staff(request, id)   # Remove employee

# Holiday Management
holidays(request)           # List holidays
add_holiday(request)        # Create holiday
delete_holiday(request, id) # Remove holiday
```

**Owner Dashboard Data Flow:**
```python
def analytics(request):
    # 1. Get selected restaurant from session
    selected_id = request.session.get("selected_restaurant_id")
    
    # 2. Fetch restaurant with owner check
    restaurant = Restaurant.objects.get(
        id=selected_id,
        owner=request.user
    )
    
    # 3. Get staff count for display [FIXED - was static $ values]
    staff_count = RestaurantStaff.objects.filter(
        restaurant=restaurant
    ).count()
    
    # 4. Get actual booking stats
    bookings = Booking.objects.filter(
        restaurant=restaurant,
        status='confirmed'
    )
    
    # 5. Calculate real revenue
    total_revenue = bookings.aggregate(
        Sum('total_price')
    )['total_price__sum'] or 0
    
    # 6. [ISSUE] Static demographics still present
    # Should be: actual customer gender distribution
    
    # 7. Render
    return render(request, "Restaurants/analytics.html", {
        "restaurant": restaurant,
        "total_staff": staff_count,
        "total_revenue": total_revenue,
        "total_bookings": bookings.count(),
        # [TODO] Replace with real data:
        "male_customers": 0,  # Currently fake
        "female_customers": 0,  # Currently fake
        # [TODO] Add approval status notification
    })
```

---

### 4. Reservations App (`/Reservations/`)
**Purpose:** Booking and customer-facing reservation features

**Views:**
```python
# Customer Booking
booking_view(request, name)     # Main booking page
    ↓
get_unavailable_tables(request) # AJAX endpoint
    ↓
placeOrder_view(request, name)  # Checkout & payment
    ↓
order_success(request, id)      # Confirmation page

# Reviews
post_review(request)              # Submit review

# Data APIs
getUnavailableTables(request)     # Real-time availability
```

**Booking Flow:**
```
GET /reservations/Restaurant-Name/
    ↓
Fetch restaurant details
    ↓
Get available tables for today
    ↓
Show reservation form
    ↓
User selects date, time, duration
    ↓
AJAX: POST /api/get-unavailable-tables/
    ↓
Server calculates unavailable tables
    ↓
Returns table IDs to disable
    ↓
User selects from available tables
    ↓
Clicks "Book Now"
    ↓
[IF NOT LOGGED IN]
    Store intent in session
    Redirect to /uh/auth/
    After login, redirect back to checkout
    ↓
[IF LOGGED IN]
    Go to checkout page
    ↓
Enter payment details
    ↓
Submit
    ↓
[Current] Mark as paid, redirect to success
[Should] Process payment, generate invoice, send email
```

**AJAX Availability Check:**
```python
def get_unavailable_tables(request, restaurant_name):
    """
    Returns table IDs that are already booked for given time slot.
    Called via AJAX when user changes date/time/duration.
    """
    restaurant = get_object_or_404(Restaurant, name=restaurant_name)
    
    # Parse parameters
    date_str = request.GET.get("date")
    start_time_str = request.GET.get("start_time")
    duration = int(request.GET.get("duration", 1))
    
    # Calculate time window
    start = datetime.strptime(f"{date_str} {start_time_str}", "%Y-%m-%d %H:%M")
    end = start + timedelta(hours=duration)
    
    # Find conflicting bookings
    unavailable = Booking.objects.filter(
        restaurant=restaurant,
        table_id__isnull=False,
        booking_start__lt=end,      # Starts before our end
        booking_end__gt=start       # Ends after our start
    ).exclude(status='cancelled').values_list('table_id', flat=True)
    
    return JsonResponse({
        'unavailable_tables': list(set(unavailable))
    })
```

---

## Services Layer

### Analytics Service (`Restaurants/Services.py`)
```python
class RestaurantAnalytics:
    @staticmethod
    def getAnalytics(restaurant_id, period='month'):
        """
        Calculate restaurant performance metrics.
        
        Returns: {
            'total_bookings': int,
            'confirmed_bookings': int,
            'cancelled_bookings': int,
            'revenue': Decimal,
            'average_party_size': float,
            'popular_tables': list,
            'booking_trend': list  # daily counts
        }
        """
        bookings = Booking.objects.filter(
            restaurant_id=restaurant_id,
            created_at__gte=timezone.now() - timedelta(days=30)
        )
        
        return {
            'total_bookings': bookings.count(),
            'confirmed': bookings.filter(status='confirmed').count(),
            'revenue': bookings.filter(
                status='confirmed'
            ).aggregate(Sum('total_price'))['total_price__sum'] or 0
        }
```

### Booking Service (`Reservations/services.py`)
```python
class BookingService:
    @staticmethod
    def create_booking(request, restaurant_name):
        """
        Create a new booking record.
        Handles validation, conflict checking, and initial creation.
        """
        # Parse form data
        date = request.POST.get("date")
        start_time = request.POST.get("start_time")
        duration = int(request.POST.get("duration", 1))
        table_ids = request.POST.getlist("tables")
        
        # Calculate times
        booking_start = datetime.strptime(
            f"{date} {start_time}", "%Y-%m-%d %H:%M"
        )
        booking_end = booking_start + timedelta(hours=duration)
        
        # Validate no conflicts
        for table_id in table_ids:
            conflicts = Booking.objects.filter(
                table_id=table_id,
                booking_start__lt=booking_end,
                booking_end__gt=booking_start
            ).exclude(status='cancelled').exists()
            
            if conflicts:
                raise ValidationError("Table already booked")
        
        # Create booking (payment pending)
        booking = Booking.objects.create(
            restaurant=restaurant,
            user=request.user,
            booking_start=booking_start,
            booking_end=booking_end,
            status='pending',
            payment_status='pending'
        )
        
        return {'booking': booking, 'total_price': calculate_price(booking)}
```

---

## Context Processors

### Owner Context (`Restaurants/context_processors.py`)
```python
def owner_context(request):
    """
    Injects owner-specific data into all templates.
    Makes restaurant data available globally for owner dashboard.
    """
    if not request.user.is_authenticated:
        return {}
    
    # Get restaurants owned by user
    owners_restaurants = Restaurant.objects.filter(owner=request.user)
    
    # Get currently selected restaurant from session
    selected_id = request.session.get("selected_restaurant_id")
    selected_restaurant = None
    
    if selected_id:
        selected_restaurant = owners_restaurants.filter(id=selected_id).first()
    
    # Default to first restaurant if none selected
    if not selected_restaurant and owners_restaurants.exists():
        selected_restaurant = owners_restaurants.first()
        request.session['selected_restaurant_id'] = selected_restaurant.id
    
    return {
        "CP__OwnerProfile": request.user,
        "CP__Restaurants": owners_restaurants,
        "CP__Selected": selected_restaurant,
    }
```

**Available in Templates:**
```html
{% if CP__Selected %}
    Managing: {{ CP__Selected.name }}
    <select onchange="switchRestaurant(this.value)">
        {% for r in CP__Restaurants %}
            <option value="{{ r.id }}">{{ r.name }}</option>
        {% endfor %}
    </select>
{% endif %}
```

---

## URL Routing

### Main URLs (`Dinesphere/urls.py`)
```python
urlpatterns = [
    # Public
    path('', include('Core.urls')),
    path('uh/', include('UsersHandling.urls')),  # Auth
    path('reservations/', include('Reservations.urls')),  # Booking
    
    # Owner/Staff
    path('business/', include('Restaurants.urls')),  # Management
    
    # Admin
    path('admin/', admin.site.urls),
]
```

### Restaurants URLs (`Restaurants/urls.py`)
```python
urlpatterns = [
    # Dashboard
    path('', views.analytics, name="analytics"),
    path('switch-business/<int:id>/', views.switch_business, name="switch-business"),
    
    # Restaurant
    path('register/', views.register_restaurant, name="register-restaurant"),
    path('edit/<int:id>/', views.edit_restaurant, name="edit-restaurant"),
    path('business-info/', views.business_info, name="business-info"),
    
    # Tables
    path('tables/', views.tables, name="tables"),
    path('add-table/', views.add_table, name="add-table"),
    path('edit-table/<int:id>/', views.edit_table, name="edit-table"),
    path('delete-table/<int:id>/', views.delete_table, name="delete-table"),
    
    # Staff
    path('staff-management/', views.staff_management, name="staff-management"),
    path('add-staff/', views.add_staff, name="add-staff"),
    path('remove-staff/<int:id>/', views.remove_staff, name="remove-staff"),
    
    # Holidays
    path('holidays/', views.holidays, name="holidays"),
    path('add-holiday/', views.add_holiday, name="add-holiday"),
    path('delete-holiday/<int:id>/', views.delete_holiday, name="delete-holiday"),
]
```

---

## Model Relationships

```python
# User ←→ Restaurant (Ownership)
User.restaurants  # Restaurant_set (owned)
Restaurant.owner  # FK to User

# User ←→ Restaurant (Staff)
User.restaurantstaff_set  # RestaurantStaff objects
Restaurant.staff  # RestaurantStaff objects

# Restaurant ←→ Table
Restaurant.tables  # Table_set
Table.restaurant  # FK

# Restaurant ←→ Booking
Restaurant.bookings  # Booking_set
Booking.restaurant  # FK

# User ←→ Booking
User.bookings  # Booking_set
Booking.user  # FK

# Table ←→ Booking
Table.bookings  # Booking_set
Booking.table  # FK (nullable)

# Restaurant ←→ Review
Restaurant.reviews  # Review_set
Review.restaurant  # FK

# User ←→ Review
User.reviews  # Review_set
Review.user  # FK

# Booking ←→ Review (Optional)
Booking.review  # OneToOne (if reviewed)
Review.booking  # FK (nullable)
```

---

## Authentication Flow

```
Request comes in
    ↓
SessionMiddleware loads session
    ↓
AuthenticationMiddleware sets request.user
    ↓
View checks @login_required
    ↓
If not authenticated:
    Redirect to /uh/auth/
    Store next URL in session
    ↓
User logs in
    ↓
session auth updated
    ↓
Redirect to stored next URL
```

---

## Issues & Improvements

### Current Issues:
1. **No API versioning** - All endpoints are direct views
2. **No rate limiting** on most endpoints (only login fixed)
3. **No caching** - Every request hits database
4. **No async processing** - Emails sent synchronously (if implemented)
5. **No request logging** - Can't trace errors

### Dev-Only Improvements (No Extra Cost):
1. **Add request logging middleware** - Track all requests
2. **Query optimization** - Use select_related, prefetch_related
3. **Template caching** - Cache rendered templates
4. **Database indexes** - Already documented in ER_MODEL.md
5. **Better error handling** - Try-except blocks in services

---

## Testing Architecture

```python
# Test structure
Tests/
├── test_views.py          # View integration tests
├── test_models.py         # Model unit tests
├── test_services.py       # Business logic tests
└── test_decorators.py     # Access control tests

# Example test
def test_booking_creation(self):
    # Setup
    user = User.objects.create_user('test', 'test@test.com', 'password123')
    restaurant = Restaurant.objects.create(name='Test', owner=user)
    
    # Execute
    booking = Booking.objects.create(
        user=user,
        restaurant=restaurant,
        booking_start=timezone.now() + timedelta(days=1),
        booking_end=timezone.now() + timedelta(days=1, hours=2)
    )
    
    # Assert
    self.assertEqual(booking.status, 'pending')
    self.assertEqual(booking.payment_status, 'pending')
```
