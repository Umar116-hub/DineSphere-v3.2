from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.cache import cache
from .models import User, CustomerProfile, RestaurantStaff
from .services import create_customer_user

# Rate limiting settings
MAX_LOGIN_ATTEMPTS = 5
LOGIN_TIMEOUT = 300  # 5 minutes in seconds

# Create your views here.

def auth(request):
    # Clear any stale messages from previous sessions
    if request.method == "GET":
        storage = messages.get_messages(request)
        storage.used = True
    return render(request, 'UsersHandling/auth.html')


def signup_user(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        dob = request.POST.get("dob")
        gender = request.POST.get("gender")
        image = request.FILES.get("image")

        if not username or not password or not email:
            messages.error(request, "All fields are required")
            return redirect("auth")

        # Password strength validation
        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long")
            return redirect("auth")
        if not any(c.isupper() for c in password):
            messages.error(request, "Password must contain at least one uppercase letter")
            return redirect("auth")
        if not any(c.islower() for c in password):
            messages.error(request, "Password must contain at least one lowercase letter")
            return redirect("auth")
        if not any(c.isdigit() for c in password):
            messages.error(request, "Password must contain at least one number")
            return redirect("auth")

        try:
            create_customer_user(
                username=username,
                email=email,
                password=password,
                dob=dob,
                gender=gender,
                image=image
            )

            messages.success(request, "Account created successfully! Please log in.")
            return redirect("login")

        except ValueError as e:
            messages.error(request, str(e))
            return redirect("auth")

        except Exception:
            messages.error(request, "Something went wrong")
            return redirect("auth")

    return redirect("auth")


# -------------------------
# 2) LOGIN USER (with rate limiting)
# -------------------------
def login_user(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        # Check rate limit
        ip_key = f"login_attempts_{request.META.get('REMOTE_ADDR', 'unknown')}"
        attempts = cache.get(ip_key, 0)
        
        if attempts >= MAX_LOGIN_ATTEMPTS:
            messages.error(request, f"Too many login attempts. Please try again after {LOGIN_TIMEOUT // 60} minutes.")
            return redirect("auth")

        if request.user.is_authenticated:
             logout(request)
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Clear failed attempts on success
            cache.delete(ip_key)
            login(request, user)
            return redirect("home")  
        else:
            # Increment failed attempts
            cache.set(ip_key, attempts + 1, LOGIN_TIMEOUT)
            remaining = MAX_LOGIN_ATTEMPTS - (attempts + 1)
            messages.error(request, f"Invalid username or password. {remaining} attempts remaining.")
            return redirect("auth")

    return redirect("auth")


def logout_user(request):
    if request.method != "POST":
        return redirect("auth")
    logout(request)
    return redirect("home")