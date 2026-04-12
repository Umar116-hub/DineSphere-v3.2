# Project Context Map

## What this project is
A  restaurant reservation web app.
- Users can browse restaurants and reserve tables
- Restaurant owners can register and manage their restaurant
- Built with: Django 6.0.3 + SQLite3 + MongoDB (for analytics)

## File Map (Key Files Only)

### Frontend (Django Templates)
- `Core/templates/Core/home.html` — Landing page with restaurant listings & search
- `Core/templates/Core/Profile.html` — User profile & favorites
- `Core/templates/Core/restaurant_card.html` — Restaurant card component
- `Reservations/templates/Reservations/booking.html` — Restaurant booking page
- `Reservations/templates/Reservations/checkout.html` — Payment/checkout page
- `Restaurants/templates/Restaurants/analytics.html` — Owner dashboard with analytics
- `Restaurants/templates/Restaurants/staff_management.html` — Staff management UI
- `Restaurants/templates/Restaurants/reservations.html` — Owner's reservation management
- `Restaurants/templates/Restaurants/tables.html` — Table management for owners
- `Restaurants/templates/Restaurants/business_info.html` — Restaurant profile editing
- `UsersHandling/templates/UsersHandling/auth.html` — Login/signup page

### Backend (Django)

**Core App** (`Core/`)
- `views.py` — Home page, user profile, favorites toggle, search
- `urls.py` — Routes: `/`, `/profile/`, `/toggle-favourite/`, `/search/`
- `utils.py` — Utility functions for availability checking

**UsersHandling App** (`UsersHandling/`)
- `views.py` — Auth (login/signup/logout), user registration
- `models.py` — `User` (custom auth model), `CustomerProfile`, `RestaurantStaff`
- `services.py` — Staff verification, add/remove staff
- `urls.py` — Routes: `/uh/auth/`, `/uh/login/`, `/uh/signup/`, `/uh/logout/`, staff management

**Restaurants App** (`Restaurants/`)
- `views.py` — Restaurant CRUD, table management, holidays, reviews, analytics, staff management
- `models.py` — `Restaurant`, `Table`, `TableSize`, `SeatingType`, `SpecialDay`, `Review`, `ReviewSummary`, `FavouriteRestaurant`, `Testimonials`
- `Services.py` — Business logic for table operations, reservations, analytics
- `urls.py` — Routes: `/business/registration/`, `/business/tables/`, `/business/reservations/`, etc.
- `forms.py` — Forms for restaurant registration and updates
- `context_processors.py` — Owner context for templates

**Reservations App** (`Reservations/`)
- `views.py` — Booking flow, checkout, place order, review posting, unavailable table checking
- `models.py` — `Booking` (reservation model with payment info)
- `services.py` — Reservation creation, availability checking, conflict detection
- `utils.py` — Table combination logic, availability utilities
- `urls.py` — Routes: `/reservation/<restaurant_name>/`, `/reservation/checkout/`, `/reservation/placeOrder/`

### Config
- `Dinesphere/settings.py` — Django settings, database (SQLite3), installed apps, middleware
- `Dinesphere/urls.py` — Root URL configuration, app routing
- `manage.py` — Django management script
- `requirements.txt` — Python dependencies (Django 6.0.3, DRF, Pillow, PyMongo)

## Known issues so far
- No known critical issues documented (audit report is empty)
- MongoDB URI is hardcoded in settings (MONGO_URI = "mongodb://localhost:27017/")
- SQLite3 used for main DB (not production-ready)

## Stack
- **Framework**: Django 6.0.3 (Python)
- **Templates**: Django Template Language (server-side rendering)
- **API**: Django REST Framework 3.17.1
- **Primary Database**: SQLite3 (dev/local)
- **Analytics Database**: MongoDB (PyMongo 4.16.0)
- **Auth**: Django Session Authentication (built-in)
- **Image Handling**: Pillow 12.2.0
- **Frontend**: Vanilla JS + Tailwind-like styling (no React/Vue)
- **Hosting**: Local development only (DEBUG=True)