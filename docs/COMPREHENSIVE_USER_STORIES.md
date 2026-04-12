# DineSphere - Comprehensive User Stories & System Design

## Table of Contents
1. [Customer User Journey](#1-customer-user-journey)
2. [Restaurant Owner User Journey](#2-restaurant-owner-user-journey)
3. [Staff User Journey](#3-staff-user-journey)
4. [Database Component Design](#4-database-component-design)
5. [Frontend-Backend Interaction](#5-frontend-backend-interaction)
6. [Test Cases](#6-test-cases)
7. [Improvement Areas](#7-improvement-areas)

---

## 1. Customer User Journey

### 1.1 Discovery Phase
**User Goal:** Find a suitable restaurant for dining

**Current Flow:**
```
Customer visits homepage
    ↓
Sees featured restaurants (top rated)
    ↓
Uses search bar OR scrolls to browse
    ↓
[PROBLEM: Search redirects to new page instead of filtering in-place]
    ↓
Clicks on a restaurant card
    ↓
Views restaurant details page
```

**Frontend Components:**
- `home.html` - Landing page with featured restaurants
- Search form with city dropdown
- Restaurant cards with image, name, rating, price

**Backend Handling:**
```python
# Core/views.py - home_page()
restaurants = Restaurant.objects.filter(is_approved=True)
# Annotates with is_favourite for authenticated users
# Combines with reviews for ratings display
```

**Issues Found:**
1. **Search UX Problem:** Search form POSTs to `/search/` which loads new page. Should use AJAX to filter in-place.
2. **No Real-time Availability:** Customers can't see live table availability before clicking
3. **Missing Filters:** No cuisine type, price range, or dietary filters

**Proposed Improvement:**
```javascript
// AJAX Search - Filter without page reload
function searchRestaurants(query, city) {
    fetch(`/api/search/?q=${query}&city=${city}`)
        .then(r => r.json())
        .then(data => updateRestaurantGrid(data));
}
```

---

### 1.2 Restaurant Details & Reviews
**User Goal:** Evaluate if restaurant meets expectations

**Current Flow:**
```
Customer on restaurant page (/reservations/Restaurant-Name/)
    ↓
Sees:
- Restaurant images, description, contact info
- Opening hours, location
- Reviews from other customers
- Available table sizes and seating types
    ↓
[ISSUE: Opening hours display not connected to actual hours]
    ↓
Reads reviews
    ↓
Can post own review if visited
```

**Frontend:**
- `reservation.html` - Shows restaurant info + booking form + reviews
- Review form with rating stars and comment

**Backend:**
```python
# Reservations/views.py - booking_view()
restaurant = get_object_or_404(Restaurant, name=Restaurant_name)
reviews = Review.objects.filter(restaurant=restaurant)
booking_data = view_all_booking(restaurant, date, start_time, end_time)
```

**Database Interaction:**
```sql
-- Fetch restaurant with related data
SELECT r.*, 
       AVG(rev.rating) as avg_rating,
       COUNT(rev.id) as review_count
FROM restaurants_restaurant r
LEFT JOIN restaurants_review rev ON rev.restaurant_id = r.id
WHERE r.name = 'Restaurant-Name' AND r.is_approved = TRUE
GROUP BY r.id
```

**Issues:**
1. **Time Display Issue:** Booking form shows ALL hours, not just open hours
2. **Review Verification:** No check if customer actually visited before reviewing

---

### 1.3 Booking Process
**User Goal:** Reserve a table for specific date/time

**Current Flow:**
```
Customer on reservation page
    ↓
Selects date from date picker
    ↓
Selects start time from dropdown [ISSUE: Shows all 24h, not open hours]
    ↓
Selects duration [FIXED: Now calculates end time properly]
    ↓
Sees available tables (AJAX fetched)
    ↓
Selects table(s)
    ↓
Clicks "Book Now"
    ↓
[IF NOT LOGGED IN] → Redirected to login
    ↓
Goes to checkout page with booking summary
```

**Frontend:**
```html
<!-- reservation.html -->
<form method="POST" action=".">
    <input type="date" name="date" required>
    <select name="start_time">
        <!-- [ISSUE] Currently shows 00:00-23:30 -->
        <!-- [SHOULD] Show only open hours -->
    </select>
    <select name="duration">
        <option value="1">1 hour</option>
        <option value="2">2 hours</option>
    </select>
    <!-- Tables populated via AJAX -->
    <div id="available-tables"></div>
</form>
```

**Backend - AJAX Fetch:**
```python
# Reservations/views.py - get_unavailable_tables()
def get_unavailable_tables(request, restaurant_name):
    restaurant = get_object_or_404(Restaurant, name=restaurant_name)
    date = request.GET.get('date')
    start_time = request.GET.get('start_time')
    duration = int(request.GET.get('duration', 1))
    
    # Calculate end time
    start = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
    end = start + timedelta(hours=duration)
    
    # Find unavailable tables
    unavailable = Booking.objects.filter(
        restaurant=restaurant,
        booking_start__lt=end,
        booking_end__gt=start
    ).values_list('table_id', flat=True)
    
    return JsonResponse({'unavailable_tables': list(unavailable)})
```

**Database Schema for Bookings:**
```sql
CREATE TABLE reservations_booking (
    id INTEGER PRIMARY KEY,
    restaurant_id INTEGER REFERENCES restaurants_restaurant(id),
    user_id INTEGER REFERENCES usershandling_user(id),
    table_id INTEGER REFERENCES restaurants_table(id),
    booking_start DATETIME,
    booking_end DATETIME,
    status VARCHAR(10), -- 'pending', 'confirmed', 'cancelled'
    payment_status VARCHAR(20), -- 'pending', 'paid'
    total_price DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Critical Issues Found:**
1. **Time Validation Missing:** No check if selected time is within opening hours
2. **Overlapping Bookings:** Race condition possible if two users book same table simultaneously
3. **No Booking Confirmation Email:** Customer gets no confirmation

---

### 1.4 Authentication Flow
**User Goal:** Create account or login to complete booking

**Current Flow:**
```
Customer clicks "Book Now" while not logged in
    ↓
System stores intended booking in session
    ↓
Redirects to /uh/auth/ (login/signup page)
    ↓
[ISSUE: Page shows previous user's success message]
    ↓
User sees Login form | Signup form
    ↓
[NEW USER] Fills signup:
    - Username, Email, Password
    - [ISSUE] No password strength indicator
    - DOB, Gender, Profile image
    ↓
System creates:
    - User record (in usershandling_user)
    - CustomerProfile record (empty initially)
    ↓
Redirects back to checkout
```

**Backend:**
```python
# UsersHandling/views.py - signup_user()
def signup_user(request):
    # [FIXED] Added password validation
    if len(password) < 8:
        messages.error(request, "Password must be 8+ characters")
    if not any(c.isupper() for c in password):
        messages.error(request, "Need uppercase letter")
    
    # Create user
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        image=image,
        date_of_birth=dob,
        gender=gender
    )
    CustomerProfile.objects.create(user=user)
```

**Database:**
```sql
-- usershandling_user table
CREATE TABLE usershandling_user (
    id INTEGER PRIMARY KEY,
    username VARCHAR(150) UNIQUE,
    email VARCHAR(254),
    password VARCHAR(128), -- Django hashed
    image VARCHAR(100),
    date_of_birth DATE,
    gender VARCHAR(10),
    is_owner BOOLEAN DEFAULT FALSE,
    is_staff BOOLEAN DEFAULT FALSE
);

-- Customer profile (extends user)
CREATE TABLE usershandling_customerprofile (
    id INTEGER PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES usershandling_user(id),
    -- Additional customer fields
);
```

**Issues:**
1. **UI Issue:** Login page shows stale success messages from previous sessions
2. **Missing:** Email verification after signup
3. **Missing:** "Continue as Guest" option for quick booking

---

### 1.5 Payment & Checkout
**User Goal:** Complete payment for reservation

**Current Flow:**
```
Customer on checkout page (/reservations/checkout/)
    ↓
Sees booking summary:
    - Restaurant name
    - Date & time
    - Table details
    - Total amount
    ↓
Enters payment details:
    - Card number [FIXED: Now accepts spaces]
    - Expiry date
    - CVV
    - Cardholder name
    ↓
Clicks "Place Order"
    ↓
[Current: Just marks booking as 'paid', no real payment]
    ↓
Redirects to success page
    ↓
[ISSUE: Claims "Confirmation email sent" but no email sent]
```

**Frontend:**
```html
<!-- checkout.html -->
<form method="POST" action="{% url 'placeOrder' restaurant.name %}">
    {% csrf_token %}
    <input type="text" name="cn" placeholder="Card Number" 
           pattern="[0-9\s]{19}" maxlength="19">
    <input type="month" name="expiry" required>
    <input type="text" name="cvv" pattern="[0-9]{3}" maxlength="3">
    <button type="submit">Place Order</button>
</form>
```

**Backend:**
```python
# Reservations/views.py - placeOrder_view()
def placeOrder_view(request, Restaurant_name):
    restaurant = get_object_or_404(Restaurant, name=Restaurant_name)
    
    # [ISSUE] No actual payment processing
    # [ISSUE] Card data should NOT be stored (PCI compliance)
    
    # Mark booking as paid
    booking.payment_status = 'paid'
    booking.status = 'confirmed'
    booking.save()
    
    # [MISSING] Send confirmation email
    # [MISSING] Generate invoice
    
    return redirect('orderSuccess', booking_id=booking.id)
```

**What Should Happen (Payment Simulation):**
```python
# Mock payment processor integration
def process_payment(card_number, expiry, cvv, amount):
    """
    In production: Integrate with Stripe/PayPal
    For testing: Simulate success/failure
    """
    # Validate card format
    cleaned_card = card_number.replace(' ', '')
    if len(cleaned_card) != 16 or not cleaned_card.isdigit():
        return {'success': False, 'error': 'Invalid card number'}
    
    # Check expiry not past
    if expiry < current_month:
        return {'success': False, 'error': 'Card expired'}
    
    # Simulate processing delay
    time.sleep(1)
    
    # Return mock transaction ID
    return {
        'success': True,
        'transaction_id': f'TXN_{uuid4().hex[:12]}',
        'amount': amount
    }
```

**Missing Features:**
1. **Invoice Generation:** No PDF invoice created after payment
2. **Email Confirmation:** No email sent to customer
3. **SMS Notification:** No text message option
4. **Payment Receipt:** No downloadable receipt

---

### 1.6 Post-Booking Management
**User Goal:** View, manage, or cancel reservation

**Current Flow:**
```
Customer visits Profile page (/profile/)
    ↓
Sees tabs:
    - Profile Info
    - Pending Orders
    - Finished Orders
    - Cancelled Orders
    ↓
Can cancel pending booking
    ↓
[ISSUE] No confirmation dialog
    ↓
[ISSUE] No refund process shown
    ↓
[ISSUE] No email notification of cancellation
```

**Database Status Flow:**
```
Booking Status Lifecycle:
PENDING → CONFIRMED (after payment)
      → CANCELLED (by user or system)
      → COMPLETED (after dining date)

Payment Status:
pending → paid → refunded (if cancelled)
```

**What Should Happen:**
```python
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    # Only allow cancel if > 24h before booking
    if booking.booking_start < timezone.now() + timedelta(hours=24):
        return JsonResponse({'error': 'Cannot cancel within 24h'}, status=400)
    
    booking.status = 'cancelled'
    booking.save()
    
    # [MISSING] Process refund if paid
    # [MISSING] Send cancellation email
    # [MISSING] Free up table for others
    
    return redirect('profile')
```

---

## 2. Restaurant Owner User Journey

### 2.1 Registration & Onboarding
**User Goal:** Register restaurant on platform

**Current Flow:**
```
Owner visits homepage
    ↓
[ISSUE] No clear "Register Restaurant" button
    ↓
Must click generic "Login" then find signup
    ↓
Fills registration form:
    - Restaurant name
    - Description
    - Location, City
    - Contact info
    - Images
    - Opening hours [ISSUE: Single time field, not proper schedule]
    ↓
Submits form
    ↓
[ISSUE] No confirmation message shown
    ↓
Restaurant created with is_approved=FALSE
    ↓
Owner redirected to... nowhere clear
```

**Database - Restaurant Creation:**
```sql
INSERT INTO restaurants_restaurant (
    name, description, location, city, 
    phone, email, image, opening_time, closing_time,
    owner_id, is_approved, created_at
) VALUES (...);

-- Creates RestaurantStaff record linking owner to restaurant
INSERT INTO restaurants_restaurantstaff (
    user_id, restaurant_id, role, is_admin
) VALUES (owner_id, restaurant_id, 'owner', TRUE);
```

**Issues:**
1. **No Clear Entry Point:** "Register Restaurant" not prominently displayed
2. **No Approval Notification:** Owner doesn't know restaurant is pending approval
3. **No Onboarding Flow:** Owner not guided to dashboard after registration

**Proposed Fix:**
```html
<!-- Add to navbar for unauthenticated users -->
<a href="/restaurant/register/" class="btn-primary">
    Register Your Restaurant
</a>

<!-- Dedicated registration page -->
<!-- Onboarding wizard: Restaurant Info → Hours → Tables → Staff -->
```

---

### 2.2 Approval & Dashboard Access
**User Goal:** Know if restaurant is approved and access dashboard

**Current Flow:**
```
Owner logs in
    ↓
Sees regular customer homepage
    ↓
[ISSUE] No indication they have a pending restaurant
    ↓
Must manually navigate to /business/
    ↓
[IF NOT APPROVED] Sees yellow banner "Pending Approval"
    ↓
[IF APPROVED] Sees analytics dashboard
    ↓
Dashboard shows:
    - [ISSUE] Static fake values ($500k revenue, etc.)
    - [ISSUE] Male/Female demographics (not relevant)
    - Total bookings count
    - Revenue stats
```

**Backend:**
```python
# Restaurants/context_processors.py
def owner_context(request):
    if request.user.is_authenticated and request.user.is_owner:
        restaurants = Restaurant.objects.filter(owner=request.user)
        return {
            'CP__OwnerProfile': request.user,
            'CP__Restaurants': restaurants,
            'CP__Selected': restaurants.first()
        }
    return {}
```

**What's Fixed:**
- ✅ Approval status banner added to analytics page

**What Still Needs Work:**
```python
# Real-time dashboard data
def get_restaurant_analytics(restaurant, period='month'):
    bookings = Booking.objects.filter(
        restaurant=restaurant,
        status='confirmed',
        booking_start__gte=timezone.now() - timedelta(days=30)
    )
    
    return {
        'total_bookings': bookings.count(),
        'revenue': bookings.aggregate(Sum('total_price')),
        'upcoming': bookings.filter(booking_start__gte=timezone.now()).count(),
        'occupancy_rate': calculate_occupancy(restaurant, period)
    }
```

---

### 2.3 Restaurant Management
**User Goal:** Manage tables, staff, reservations, holidays

**Current Flow - Tables:**
```
Owner navigates to /business/tables/
    ↓
Sees list of existing tables
    ↓
Can add new table:
    - Table number
    - Capacity
    - Seating type (indoor/outdoor/patio)
    - Table size category
    ↓
[ISSUE] Table layout not visual (just list)
    ↓
Can edit/delete tables
```

**Current Flow - Staff Management:**
```
Owner navigates to /business/staff-management/
    ↓
[ISSUE] Page shows "Label" and "Budget" filters (irrelevant)
    ↓
Sees current staff list
    ↓
Can add staff:
    - Select user (by username)
    - Assign role (manager/waiter/host)
    ↓
[ISSUE] No way to see staff availability/schedule
```

**Current Flow - Reservations:**
```
Owner navigates to /business/reservations/
    ↓
Sees all bookings for restaurant
    ↓
Can filter by:
    - Date range
    - Status
    ↓
Can approve/reject pending bookings
    ↓
[ISSUE] No customer contact info shown
```

**Current Flow - Holidays:**
```
Owner navigates to /business/holidays/
    ↓
Can add special dates:
    - Holiday name
    - Date
    - Is closed (full day)
    - Or special hours
    ↓
[ISSUE] Static fake stats ($500k) shown on page
```

**Database Design:**
```sql
-- Tables
CREATE TABLE restaurants_table (
    id INTEGER PRIMARY KEY,
    restaurant_id INTEGER REFERENCES restaurants_restaurant(id),
    table_number VARCHAR(10),
    capacity INTEGER,
    seating_type VARCHAR(20), -- 'indoor', 'outdoor', 'patio'
    size_category VARCHAR(20), -- 'small', 'medium', 'large'
    is_active BOOLEAN DEFAULT TRUE
);

-- Staff
CREATE TABLE restaurants_restaurantstaff (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES usershandling_user(id),
    restaurant_id INTEGER REFERENCES restaurants_restaurant(id),
    role VARCHAR(20), -- 'owner', 'manager', 'waiter', 'host'
    is_admin BOOLEAN DEFAULT FALSE,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Holidays
CREATE TABLE restaurants_holiday (
    id INTEGER PRIMARY KEY,
    restaurant_id INTEGER REFERENCES restaurants_restaurant(id),
    name VARCHAR(100),
    date DATE,
    is_closed BOOLEAN DEFAULT TRUE,
    special_opening TIME NULL,
    special_closing TIME NULL
);
```

---

## 3. Staff User Journey

### 3.1 Staff Member Flow
**User Goal:** Assist with restaurant operations

**Current Design Issues:**
```
[CRITICAL ISSUE] Staff have NO dedicated interface
    ↓
Staff login sees same as customers
    ↓
Staff must be given direct URLs to access:
    - /business/reservations/
    - /business/tables/
    ↓
No role-based access control enforced
```

**What Should Exist:**
```python
# Staff dashboard with limited access
def staff_dashboard(request):
    staff = RestaurantStaff.objects.get(user=request.user)
    restaurant = staff.restaurant
    
    if staff.role == 'host':
        # Only see today's reservations and check-ins
        bookings = Booking.objects.filter(
            restaurant=restaurant,
            booking_start__date=timezone.now().date()
        )
        return render(request, 'staff/checkin.html', {'bookings': bookings})
    
    elif staff.role == 'manager':
        # See all reservations but not analytics/settings
        bookings = Booking.objects.filter(restaurant=restaurant)
        return render(request, 'staff/manager_dashboard.html', {...})
```

---

## 4. Database Component Design

### 4.1 Entity Relationship Diagram
```
[User] 1:1 [CustomerProfile]
  |
  | 1:N
  v
[Restaurant] 1:N [Table]
  |              |
  | 1:N          | 1:N
  v              v
[RestaurantStaff] [Booking] 1:N [Review]
  |
  | N:M (through)
  v
[User]
```

### 4.2 Core Tables

**Users & Authentication:**
```sql
-- Custom User model (extends AbstractUser)
CREATE TABLE usershandling_user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    password VARCHAR(128) NOT NULL,
    last_login DATETIME,
    is_superuser BOOLEAN DEFAULT FALSE,
    username VARCHAR(150) UNIQUE NOT NULL,
    first_name VARCHAR(150),
    last_name VARCHAR(150),
    email VARCHAR(254),
    is_staff BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    date_joined DATETIME DEFAULT CURRENT_TIMESTAMP,
    -- Custom fields
    image VARCHAR(100),
    date_of_birth DATE,
    gender VARCHAR(10),
    is_owner BOOLEAN DEFAULT FALSE,
    phone VARCHAR(20)
);

CREATE TABLE usershandling_customerprofile (
    id INTEGER PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES usershandling_user(id),
    preferences TEXT, -- JSON field for dietary preferences
    total_bookings INTEGER DEFAULT 0,
    total_spent DECIMAL(10,2) DEFAULT 0.00
);
```

**Restaurant Management:**
```sql
CREATE TABLE restaurants_restaurant (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    location VARCHAR(200),
    city VARCHAR(50),
    phone VARCHAR(20),
    email VARCHAR(254),
    image VARCHAR(100),
    opening_time TIME,
    closing_time TIME,
    owner_id INTEGER REFERENCES usershandling_user(id),
    is_approved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE restaurants_table (
    id INTEGER PRIMARY KEY,
    restaurant_id INTEGER NOT NULL REFERENCES restaurants_restaurant(id),
    table_number VARCHAR(10) NOT NULL,
    capacity INTEGER NOT NULL,
    seating_type VARCHAR(20) DEFAULT 'indoor',
    size_category VARCHAR(20) DEFAULT 'medium',
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(restaurant_id, table_number)
);

CREATE TABLE restaurants_seatingtype (
    id INTEGER PRIMARY KEY,
    restaurant_id INTEGER REFERENCES restaurants_restaurant(id),
    name VARCHAR(50),
    description VARCHAR(200)
);

CREATE TABLE restaurants_tablesize (
    id INTEGER PRIMARY KEY,
    restaurant_id INTEGER REFERENCES restaurants_restaurant(id),
    name VARCHAR(50),
    min_capacity INTEGER,
    max_capacity INTEGER
);
```

**Bookings & Reservations:**
```sql
CREATE TABLE reservations_booking (
    id INTEGER PRIMARY KEY,
    restaurant_id INTEGER NOT NULL REFERENCES restaurants_restaurant(id),
    user_id INTEGER NOT NULL REFERENCES usershandling_user(id),
    table_id INTEGER REFERENCES restaurants_table(id),
    booking_start DATETIME NOT NULL,
    booking_end DATETIME NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- pending, confirmed, cancelled, completed
    payment_status VARCHAR(20) DEFAULT 'pending', -- pending, paid, refunded
    total_price DECIMAL(10,2) DEFAULT 0.00,
    guest_count INTEGER,
    special_requests TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE reservations_review (
    id INTEGER PRIMARY KEY,
    restaurant_id INTEGER NOT NULL REFERENCES restaurants_restaurant(id),
    user_id INTEGER NOT NULL REFERENCES usershandling_user(id),
    booking_id INTEGER REFERENCES reservations_booking(id),
    rating INTEGER CHECK(rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Staff Management:**
```sql
CREATE TABLE restaurants_restaurantstaff (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES usershandling_user(id),
    restaurant_id INTEGER NOT NULL REFERENCES restaurants_restaurant(id),
    role VARCHAR(20) DEFAULT 'staff', -- owner, manager, host, waiter, chef
    is_admin BOOLEAN DEFAULT FALSE,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, restaurant_id)
);

CREATE TABLE restaurants_holiday (
    id INTEGER PRIMARY KEY,
    restaurant_id INTEGER NOT NULL REFERENCES restaurants_restaurant(id),
    name VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    is_closed BOOLEAN DEFAULT TRUE,
    special_opening TIME,
    special_closing TIME
);

CREATE TABLE restaurants_favouriterestaurant (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES usershandling_user(id),
    restaurant_id INTEGER NOT NULL REFERENCES restaurants_restaurant(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, restaurant_id)
);
```

### 4.3 Indexes for Performance
```sql
-- Search optimization
CREATE INDEX idx_restaurant_city ON restaurants_restaurant(city);
CREATE INDEX idx_restaurant_approved ON restaurants_restaurant(is_approved);

-- Booking queries
CREATE INDEX idx_booking_restaurant_date ON reservations_booking(restaurant_id, booking_start);
CREATE INDEX idx_booking_user ON reservations_booking(user_id);
CREATE INDEX idx_booking_status ON reservations_booking(status);

-- Review queries
CREATE INDEX idx_review_restaurant ON reservations_review(restaurant_id);

-- Staff lookups
CREATE INDEX idx_staff_user ON restaurants_restaurantstaff(user_id);
CREATE INDEX idx_staff_restaurant ON restaurants_restaurantstaff(restaurant_id);
```

---

## 5. Frontend-Backend Interaction

### 5.1 Request Flow Architecture
```
User Action
    ↓
Template (HTML + DTL)
    ↓
JavaScript (Event Handling)
    ↓
[AJAX Request] or [Form POST]
    ↓
URL Router (urls.py)
    ↓
View Function (views.py)
    ↓
Authentication Check (@login_required, @restrict_access)
    ↓
Business Logic / Services
    ↓
Models (ORM Queries)
    ↓
Database
    ↓
Response (HTML Template / JSON)
    ↓
Template Rendering
    ↓
User Display
```

### 5.2 Key API Endpoints
```python
# Customer APIs
GET    /api/restaurants/?city=&search=
GET    /api/restaurant/<id>/availability/?date=&time=&guests=
POST   /api/bookings/              # Create booking
GET    /api/bookings/<id>/
PATCH  /api/bookings/<id>/cancel/
POST   /api/reviews/               # Post review

# Owner APIs
GET    /api/owner/restaurants/
GET    /api/owner/analytics/?restaurant_id=&period=
GET    /api/owner/bookings/?restaurant_id=&status=
POST   /api/owner/tables/
POST   /api/owner/staff/
POST   /api/owner/holidays/

# Authentication
POST   /api/auth/login/
POST   /api/auth/signup/
POST   /api/auth/logout/
POST   /api/auth/password-reset/
```

### 5.3 Data Flow Examples

**Search Restaurants:**
```javascript
// Frontend (home.html)
async function searchRestaurants() {
    const response = await fetch('/api/restaurants/?city=NewYork&search=italian');
    const data = await response.json();
    renderRestaurantCards(data.results);
}
```

```python
# Backend (Core/views.py)
def search_restaurants(request):
    city = request.GET.get('city')
    query = request.GET.get('search')
    
    restaurants = Restaurant.objects.filter(
        is_approved=True,
        city__icontains=city,
        name__icontains=query
    ).annotate(
        avg_rating=Avg('review__rating'),
        review_count=Count('review')
    )
    
    return JsonResponse({
        'results': [r.to_dict() for r in restaurants]
    })
```

---

## 6. Test Cases

### 6.1 Customer Test Cases

| ID | Scenario | Steps | Expected | Status |
|----|----------|-------|----------|--------|
| TC-C-001 | Search with filters | Enter city, click search | Results filter in-place | FAIL (redirects) |
| TC-C-002 | View restaurant details | Click restaurant card | Shows info, reviews, hours | PASS |
| TC-C-003 | Check reviews | Scroll to reviews section | Reviews load with ratings | PASS |
| TC-C-004 | Booking time validation | Select 3 AM for closed restaurant | Error: "Restaurant closed" | FAIL (no validation) |
| TC-C-005 | Booking without login | Click "Book Now" as guest | Redirect to login with return URL | PASS |
| TC-C-006 | Registration | Fill signup form | Account created, logged in | PASS |
| TC-C-007 | Weak password | Enter "123" as password | Error: Password too weak | PASS (now fixed) |
| TC-C-008 | Checkout flow | Enter card details | Payment processed, booking confirmed | PARTIAL (no real payment) |
| TC-C-009 | Invoice generation | After payment | PDF invoice downloadable | FAIL (not implemented) |
| TC-C-010 | Email confirmation | After booking | Email received with details | FAIL (not implemented) |
| TC-C-011 | Cancel booking | Click cancel on pending booking | Status changed, refund processed | PARTIAL (no refund) |
| TC-C-012 | View profile | Navigate to /profile/ | Shows bookings in correct tabs | PASS |
| TC-C-013 | Add favorite | Click heart icon | Added to favorites list | PASS |

### 6.2 Owner Test Cases

| ID | Scenario | Steps | Expected | Status |
|----|----------|-------|----------|--------|
| TC-O-001 | Find registration | Look for "Register Restaurant" | Button clearly visible | FAIL (buried) |
| TC-O-002 | Register restaurant | Fill form, submit | Restaurant created, pending approval | PASS |
| TC-O-003 | Approval notification | Check after registration | Sees "Pending Approval" banner | PASS |
| TC-O-004 | Access dashboard | Navigate to /business/ | Analytics dashboard loads | PASS |
| TC-O-005 | Real-time stats | View dashboard | Shows actual data, not static | FAIL (shows $500k fake) |
| TC-O-006 | Add table | Click "Add Table", fill form | Table appears in list | PASS |
| TC-O-007 | Visual table layout | View tables page | Drag-drop table layout | FAIL (just list) |
| TC-O-008 | Add staff | Navigate to staff management | Can add by username | PASS |
| TC-O-009 | Staff permissions | Login as staff | Sees limited dashboard | FAIL (no staff interface) |
| TC-O-010 | View reservations | Navigate to reservations | Shows all bookings | PASS |
| TC-O-011 | Add holiday | Add closed date | Holiday saved, bookings blocked | PARTIAL (no enforcement) |
| TC-O-012 | Update business info | Edit restaurant details | Changes saved successfully | PASS |

### 6.3 Security Test Cases

| ID | Scenario | Test | Expected | Status |
|----|----------|------|----------|--------|
| TC-S-001 | Brute force protection | Try login 5+ times | Account locked temporarily | PASS (now fixed) |
| TC-S-002 | Password strength | Use weak password | Registration rejected | PASS (now fixed) |
| TC-S-003 | Unauthorized access | Access /business/ as customer | Redirect or 403 | PASS |
| TC-S-004 | SQL injection | Search with `' OR 1=1 --` | No error, safe query | PASS (Django ORM) |
| TC-S-005 | XSS prevention | Post review with `<script>` | Script not executed | NEEDS TESTING |
| TC-S-006 | CSRF protection | Submit form without token | 403 Forbidden | PASS |

---

## 7. Improvement Areas

### 7.1 Critical (Must Fix)
1. **Search UX** - Change from page redirect to AJAX in-place filtering
2. **Time Validation** - Only show open hours in booking dropdown
3. **Payment Integration** - Add Stripe/PayPal for real payments
4. **Email System** - Send confirmation/cancellation emails
5. **Staff Interface** - Create dedicated staff dashboard with role-based access

### 7.2 High Priority
1. **Real-time Availability** - WebSocket for live table updates
2. **Invoice Generation** - PDF generation after payment
3. **Mobile App** - Responsive design issues on mobile
4. **Review Verification** - Only allow reviews after actual visit
5. **Notification System** - Push/SMS notifications

### 7.3 Medium Priority
1. **Visual Table Layout** - Drag-drop floor plan editor
2. **Analytics Dashboard** - Real data instead of static values
3. **Booking Widget** - Embeddable widget for restaurant websites
4. **Loyalty Program** - Points system for frequent diners
5. **Gift Cards** - Purchase and redeem gift cards

### 7.4 Database Improvements
1. Add `is_deleted` soft delete to all tables
2. Add database indexes for common queries
3. Implement read replicas for heavy analytics
4. Archive old bookings to separate table
5. Add full-text search for restaurant descriptions

---

## Appendix: Current vs Ideal Architecture

### Current (Simplified)
```
Browser → Django Views → Models → SQLite
                ↓
            Templates
```

### Ideal (Production)
```
Browser → Nginx → Gunicorn → Django
                ↓
            Redis (Cache/Sessions)
                ↓
            PostgreSQL (Primary)
                ↓
            MongoDB (Analytics/Logs)
                ↓
            Celery (Background Tasks)
                ↓
            RabbitMQ (Message Queue)
                ↓
            SendGrid/AWS SES (Email)
```
