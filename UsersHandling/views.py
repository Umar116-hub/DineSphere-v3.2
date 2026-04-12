from django.shortcuts import render, redirect
from django.urls import reverse
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
    
    # Check if we were redirected with a specific mode or next destination
    initial_mode = request.GET.get('mode', 'login')
    next_url = request.GET.get('next', '')
    
    return render(request, 'UsersHandling/auth.html', {
        'active_mode': initial_mode,
        'next_url': next_url
    })


def signup_user(request):
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    
    if request.method == "POST":
        username = request.POST.get("signup_username")
        email = request.POST.get("signup_email")
        password = request.POST.get("signup_password")
        dob = request.POST.get("dob")
        gender = request.POST.get("gender")
        image = request.FILES.get("image")
        intent = request.POST.get("intent", "")  # 'owner' or blank

        # Helper to handle error response
        def handle_error(msg):
            if is_ajax:
                from django.http import JsonResponse
                return JsonResponse({'success': False, 'error': msg})
            
            messages.error(request, msg)
            # Instead of redirecting, we render to preserve the POST data in the context
            return render(request, 'UsersHandling/auth.html', {
                'username': username,
                'email': email,
                'dob': dob,
                'gender': gender,
                'next_url': request.POST.get('next') or request.GET.get('next', ''),
                'active_mode': 'owner' if intent == 'owner' else 'signup'
            })

        if not username or not password or not email:
            return handle_error("All fields are required")

        # Password strength validation (Backend safety check)
        if len(password) < 8:
            return handle_error("Password must be at least 8 characters long")
        if not any(c.isupper() for c in password):
            return handle_error("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in password):
            return handle_error("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in password):
            return handle_error("Password must contain at least one number")

        try:
            from .services import create_owner_user
            if intent == 'owner':
                user = create_owner_user(username, email, password)
            else:
                user = create_customer_user(username, email, password)

            # Link details common to both
            user.date_of_birth = dob
            user.gender = gender
            if image:
                user.image = image
            user.save()

            if is_ajax:
                from django.http import JsonResponse
                login(request, user)
                return JsonResponse({'success': True})

            if intent == 'owner':
                login(request, user)
                messages.success(request, "Business account created! Please register your restaurant.")
                return redirect("restaurant_registration")
            else:
                login(request, user)
                messages.success(request, "Account created successfully!")
                next_url = request.POST.get('next') or request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect("home")

        except ValueError as e:
            return handle_error(str(e))
        except Exception:
            return handle_error("An unexpected error occurred. Please try again.")

    return redirect("auth")


# -------------------------
# 2) LOGIN USER (with rate limiting and AJAX support)
# -------------------------
def login_user(request):
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    
    if request.method == "POST":
        username = request.POST.get("login_username")
        password = request.POST.get("login_password")
        
        # Check rate limit
        ip_key = f"login_attempts_{request.META.get('REMOTE_ADDR', 'unknown')}"
        attempts = cache.get(ip_key, 0)
        
        if attempts >= MAX_LOGIN_ATTEMPTS:
            msg = f"Too many login attempts. Please try again after {LOGIN_TIMEOUT // 60} minutes."
            next_url = request.POST.get('next') or request.GET.get('next', '')
            if is_ajax:
                from django.http import JsonResponse
                return JsonResponse({'success': False, 'error': msg, 'next': next_url})
            messages.error(request, msg)
            return redirect(f"{reverse('auth')}?next={next_url}")

        if request.user.is_authenticated:
             logout(request)
             
        user = authenticate(request, username=username, password=password)
        if user is not None:
            cache.delete(ip_key)
            login(request, user)
            
            next_url = request.POST.get('next') or request.GET.get('next')
            
            if is_ajax:
                from django.http import JsonResponse
                return JsonResponse({'success': True, 'next': next_url})
            
            if next_url:
                return redirect(next_url)
                
            return redirect("home")  
        else:
            cache.set(ip_key, attempts + 1, LOGIN_TIMEOUT)
            remaining = MAX_LOGIN_ATTEMPTS - (attempts + 1)
            msg = f"Invalid username or password. {remaining} attempts remaining."
            next_url = request.POST.get('next') or request.GET.get('next', '')
            
            if is_ajax:
                from django.http import JsonResponse
                return JsonResponse({'success': False, 'error': msg, 'next': next_url})
                
            messages.error(request, msg)
            return redirect(f"{reverse('auth')}?next={next_url}")

    return redirect("auth")


def logout_user(request):
    if request.method != "POST":
        return redirect("auth")
    logout(request)
    request.session.flush()
    return redirect("home")