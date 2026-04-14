from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import User, CustomerProfile, RestaurantStaff
from .services import create_customer_user, create_owner_user



# Create your views here.

def business_register(request):
    """Dedicated combined business registration: owner account + restaurant in one flow."""
    if request.method == "GET":
        # If already logged in as owner, skip to restaurant registration
        if request.user.is_authenticated and request.user.role == 'OWNER':
            return redirect('restaurant_registration')
        return render(request, 'UsersHandling/business_register.html')

    if request.method == "POST":
        # --- Step 1: Extract owner account fields ---
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        dob = request.POST.get("dob") or None
        gender = request.POST.get("gender") or None
        image = request.FILES.get("image")

        # --- Step 2: Extract restaurant fields ---
        res_name = request.POST.get("res_name", "").strip()
        res_title = request.POST.get("res_title", "").strip()
        city = request.POST.get("city", "").strip()

        def render_with_error(msg):
            messages.error(request, msg)
            return render(request, 'UsersHandling/business_register.html', {
                'username': username, 'email': email, 'dob': dob, 'gender': gender,
            })

        # --- Validations ---
        if not username or not email or not password:
            return render_with_error("Username, email and password are required.")
        if not res_name:
            return render_with_error("Restaurant name is required.")
        if not city:
            return render_with_error("City is required.")

        # Password strength
        if len(password) < 8:
            return render_with_error("Password must be at least 8 characters.")
        if not any(c.isupper() for c in password):
            return render_with_error("Password must contain at least one uppercase letter.")
        if not any(c.islower() for c in password):
            return render_with_error("Password must contain at least one lowercase letter.")
        if not any(c.isdigit() for c in password):
            return render_with_error("Password must contain at least one number.")

        try:
            from datetime import datetime

            # 1. Create owner user
            user = create_owner_user(username, email, password)
            user.date_of_birth = dob
            user.gender = gender
            if image:
                user.image = image
            user.save()

            # 2. Create restaurant
            open_hour_str = request.POST.get("open_hour", "18:00")
            close_hour_str = request.POST.get("close_hour", "01:00")

            from Restaurants.Services import create_restaurant_for_user
            restaurant_data = {
                "name": res_name,
                "title": res_title or res_name,
                "image": request.FILES.get("res_image"),
                "about": request.POST.get("res_about", ""),
                "city": city,
                "address": request.POST.get("address", ""),
                "phone": request.POST.get("phone", ""),
                "opening_hour": datetime.strptime(open_hour_str, "%H:%M").time(),
                "closing_hour": datetime.strptime(close_hour_str, "%H:%M").time(),
                "cooldown": int(request.POST.get("cooldown") or 30),
                "slot_duration": int(request.POST.get("slot_duration") or 60),
                "advance_days": int(request.POST.get("advance_days") or 60),
                "fb_link": request.POST.get("fb_link", ""),
                "web_link": request.POST.get("web_link", ""),
            }

            restaurant = create_restaurant_for_user(user, restaurant_data)

            # 3. Log in the new owner and redirect to dashboard
            login(request, user)
            request.session["selected_restaurant_id"] = restaurant.id
            messages.success(request, f"Welcome! Your business '{restaurant.name}' has been registered successfully.")
            return redirect("analytics")

        except ValueError as e:
            return render_with_error(str(e))
        except Exception as e:
            return render_with_error(f"Registration failed: {str(e)}")

    return redirect("business_register")


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
        

        if request.user.is_authenticated:
             logout(request)
             
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            next_url = request.POST.get('next') or request.GET.get('next')
            
            if is_ajax:
                from django.http import JsonResponse
                return JsonResponse({'success': True, 'next': next_url})
            
            if next_url:
                return redirect(next_url)
                
            return redirect("home")  
        else:
            msg = "Invalid username or password."
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