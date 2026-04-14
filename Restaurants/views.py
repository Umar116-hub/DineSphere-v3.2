from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from Reservations.models import Booking
from .Services import (
    create_restaurant_for_user,
    add_table,
    getForm,
    perform_dynamic_update,
    getAnalytics,
    isStaff,
)
from UsersHandling.services import (
    add_restaurant_staff,
    get_current_restaurant_staff,
)
from .forms import TableForm, RestaurantForm, SpecialDayForm, ReviewForm
from .models import Restaurant, Table, SpecialDay, Review, SeatingType
import json
from django.contrib.auth.decorators import login_required
from UsersHandling.models import RestaurantStaff
from .services.logger import log_event
from .services.parser import get_user_logs, format_logs_to_text
from .decorators import restrict_access


# Create your views here.



@login_required
def registration(request):
    if request.method == "POST":
        try:
            data = {
                "name": request.POST.get("res_name"),
                "title": request.POST.get("res_title"),
                "image": request.FILES.get("res_image"),
                "about": request.POST.get("res_about"),
                "city": request.POST.get("city"),
                "opening_hour": datetime.strptime(
                    request.POST.get("open_hour"), "%H:%M"
                ).time(),
                "closing_hour": datetime.strptime(
                    request.POST.get("close_hour"), "%H:%M"
                ).time(),
            }

            restaurant = create_restaurant_for_user(request.user, data)

            # Set session for immediate dashboard access
            request.session["selected_restaurant_id"] = restaurant.id

            messages.success(request, f"Restaurant '{restaurant.name}' registered successfully! Welcome to your dashboard.")
            log_event(
                request.user.username,
                {
                    "action": "registered_restaurant",
                    "details": f"Registered restaurant {restaurant.name} (ID: {restaurant.id})",
                }
            )
            return redirect("analytics")

        except Exception as e:
            messages.error(request, f"Registration failed: {str(e)}")
            return redirect("restaurant_registration")
    seating_types = SeatingType.objects.all()
    if request.user.is_authenticated:
        return render(
        request, "Restaurants/registration.html", {"seatingtype": seating_types}
    )
    else:
        return redirect("/uh/auth/")


@restrict_access
def staff_management(request):
    # 1. Get the current restaurant ID from the session
    restaurant_id = request.session.get("selected_restaurant_id")

    if isStaff(request.user):
        staff = RestaurantStaff.objects.get(user=request.user)
        restaurant_id = staff.restaurant.id

    if not restaurant_id:

        messages.error(request, "Please select a restaurant first.")
        return redirect("/")  # Or wherever your restaurant selector is

    # --- HANDLE POST (Add Staff) ---
    if request.method == "POST":
        add_restaurant_staff(request)
        log_event(
            request.user.username,
            {
                "action": "registered_new_staff",
                "details": f"Registered new staff member for restaurant ID {restaurant_id}",
            },
        )
        return redirect("/business/staff-management/")

    # --- HANDLE GET (List Staff) ---
    # We use select_related('user') to get the names/images without extra DB hits
    staff_members = RestaurantStaff.objects.filter(
        restaurant_id=restaurant_id
    ).select_related("user")

    context = {"workers": staff_members, "current_restaurant_id": restaurant_id}

    return render(request, "Restaurants/staff_management.html", context)

@restrict_access
def analytics(request, tab=None):
    # NEW: Handle Form Submission
    if request.method == "POST":
    # 1. Identify which form we are processing from the hidden input
        active_tab = request.POST.get('active_tab_name')
        
        if active_tab:
            # 2. Bind the POST data to the specific form class
            form = getForm(active_tab, data=request.POST)
            
            # 3. Validate and Save
            if form and form.is_valid():
                form.save()
            # Success! Redirect to clear the POST data and the dynamic tab
        return redirect("analytics")
            

    staff = RestaurantStaff.objects.filter(user=request.user, role="OWNER").first()
    if not staff:
        messages.error(
            request,
            "You need to register a restaurant to access the Business Dashboard."
        )
        return redirect("restaurant_registration")
    restaurants = Restaurant.objects.filter(
        restaurantstaff__in=RestaurantStaff.objects.filter(user=request.user)
    ).distinct()
    restaurant_id = request.session.get("selected_restaurant_id")
    
    # Get real analytics data instead of fake static values
    from django.db.models import Sum, Count, Avg
    from django.utils import timezone
    from datetime import timedelta
    
    # Get real analytics data
    if restaurant_id:
        analytics_data = getAnalytics(restaurant_id)
        context = analytics_data
        
        # Add gender stats (demo data for now until models support it)
        context.update({
            'female_count': 124, # placeholders for now
            'male_count': 156,
            'other_count': 12,
            'female_percent': 42,
            'male_percent': 54,
        })
    else:
        context = {}
    
    context["restaurants"] = restaurants

    # Add restaurant approval status notification
    if restaurant_id:
        selected_restaurant = Restaurant.objects.filter(id=restaurant_id).first()
        if selected_restaurant:
            context["restaurant_approval_status"] = {
                "is_approved": selected_restaurant.is_approved,
                "name": selected_restaurant.name,
                "message": "Your restaurant is approved and visible to customers." if selected_restaurant.is_approved else "Your restaurant is pending approval. It will be visible after admin review."
            }

    restaurant_staff = get_current_restaurant_staff(restaurant_id)
    context["all_staff"] = restaurant_staff

    if tab:
        try:
            context["form"] = getForm(tab)
            context["active_dynamic_tab"] = tab
        except ValueError:
            pass

    return render(request, "Restaurants/analytics.html", context)

@restrict_access
def tables(request):
    restaurant_id = request.session.get("selected_restaurant_id")
    if not restaurant_id:
        messages.error(request, "Please select a restaurant first.")
        return redirect("analytics")
        
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    if request.method == "GET":
        form = TableForm(restaurant=restaurant)
        return render(request, "Restaurants/tables.html", {"form": form})
    elif request.method == "POST":
        form, success = add_table(request, restaurant_id)
        if success:
            messages.success(request, "Table added successfully!")
            return redirect("/business/tables/")
        else:
            messages.error(request, "Failed to add table. Please check the form for errors.")
            # We return render instead of redirect to keep the form object (and its errors) alive
            return render(request, "Restaurants/tables.html", {"form": form})


@restrict_access
def holidays(request):
    restaurant_id = request.session.get("selected_restaurant_id")
    if not restaurant_id:
        return redirect("/business/registration/")
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)

    if request.method == "GET":
        form = SpecialDayForm()
        special_days = SpecialDay.objects.filter(restaurant=restaurant)

        return render(
            request,
            "Restaurants/holidays.html",
            {"form": form, "special_days": special_days},
        )

    elif request.method == "POST":
        form = SpecialDayForm(request.POST)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.restaurant = restaurant  # REQUIRED
            obj.save()
            log_event(
                request.user.username,
                {
                    "action": "added_holiday",
                    "details": f"Added holiday {obj.name} (ID: {obj.id}) to restaurant ID {restaurant_id}",
                },
            )
            messages.success(request, "Holiday added successfully!")
            return redirect("/business/holidays/")
        else:
            messages.error(request, "Failed to add holiday.")
            special_days = SpecialDay.objects.filter(restaurant=restaurant)
            return render(
                request,
                "Restaurants/holidays.html",
                {"form": form, "special_days": special_days},
            )

@restrict_access
def reviews(request):
    restaurant_id = request.session["selected_restaurant_id"]
    restaurant = Restaurant.objects.get(id=restaurant_id)

    if request.method == "GET":
        form = ReviewForm()
        reviews = Review.objects.filter(restaurant=restaurant)

        return render(
            request, "Restaurants/reviews.html", {"form": form, "reviews": reviews}
        )

    elif request.method == "POST":
        form = ReviewForm(request.POST)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.restaurant = restaurant
            obj.user = request.user if request.user.is_authenticated else None
            obj.save()

            messages.success(request, "Review added successfully!")
            return redirect("/business/reviews/")
        else:
            messages.error(request, "Failed to add review. Please check the form.")
            reviews_list = Review.objects.filter(restaurant=restaurant)
            return render(
                request, "Restaurants/reviews.html", {"form": form, "reviews": reviews_list}
            )

@restrict_access
def business_info(request):
    if request.method == "GET":
        form = RestaurantForm()
        return render(request, "Restaurants/business_info.html", {"form": form})

    elif request.method == "POST":
        form = RestaurantForm(request.POST, request.FILES)

        if form.is_valid():
            restaurant = form.save()

            # optional: store in session (since you're using it elsewhere)
            request.session["selected_restaurant_id"] = restaurant.id
            RestaurantStaff.objects.create(
                user=request.user,  # current logged-in user
                restaurant=restaurant,
                role="OWNER",
                is_premium=False,  # or True if needed
            )

            messages.success(request, "Restaurant added successfully!")
            log_event(
                request.user.username,
                {
                    "action": "added_restaurant",
                    "details": f"Added restaurant {restaurant.name} (ID: {restaurant.id})",
                },
            )
        else:
            messages.error(request, "Failed to add restaurant.")

        return redirect("/business/business-info/")

@restrict_access
def reservations(request):
    restaurant_id = request.session.get("selected_restaurant_id")
    if not restaurant_id:
        return redirect("/business/registration/")
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    all_reservations = Booking.objects.filter(restaurant=restaurant)
    return render(
        request, "Restaurants/reservations.html", {"reservations": all_reservations}
    )

@restrict_access
def switch_business(request):
    if request.method == "POST":
        data = json.loads(request.body)
        business_id = data.get("business_id")

        # MUST MATCH the Context Processor key: "selected_restaurant_id"
        request.session["selected_restaurant_id"] = business_id

        # Get the name to send back to JS
        restaurant = Restaurant.objects.filter(id=business_id).first()
        name = restaurant.name if restaurant else "Unknown"

        return JsonResponse({"status": "success", "new_name": name})

@restrict_access
def reservations(request):
    restaurant_id = request.session.get("selected_restaurant_id")
    if not restaurant_id:
        return redirect("/business/registration/")
    
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    
    # 1. Trigger Auto-Approve (Lazy logic)
    from .Services import auto_approve_bookings
    auto_approve_bookings(restaurant_id)
    
    # 2. Basic Query
    reservations_query = Booking.objects.filter(restaurant=restaurant)
    
    # 3. Filtering
    status_filter = request.GET.get('status') # 'finished' (Approved) or 'pending'
    if status_filter:
        reservations_query = reservations_query.filter(status=status_filter)
        
    # 4. Sorting
    sort_by = request.GET.get('sort', 'created_at') # 'created_at' (Time Made) or 'total_price' (Price)
    if sort_by == 'price':
        reservations_query = reservations_query.order_by('-total_price') # Highest first
    else:
        # Default: Time Made (Newest first)
        reservations_query = reservations_query.order_by('-created_at')
    
    return render(
        request, "Restaurants/reservations.html", {
            "reservations": reservations_query,
            "current_status": status_filter,
            "current_sort": sort_by
        }
    )


# -------------------------------
# Mark Booking as Approved (Finished)
# -------------------------------
@restrict_access
def markfinish(request):
    if request.method == "POST":
        booking_id = request.POST.get("booking_id")
        booking = get_object_or_404(Booking, id=booking_id)

        try:
            if booking.approve():
                # We could send an "Approved" email here if requested
                messages.success(request, "Booking approved successfully.")
            else:
                messages.info(request, "Booking was already approved or cancelled.")
        except Exception as e:
            messages.error(request, str(e))

    return redirect(request.META.get("HTTP_REFERER", "/"))


# -------------------------------
# Mark Booking as Cancelled
# -------------------------------
@restrict_access
def markcancel(request):
    if request.method == "POST":
        booking_id = request.POST.get("booking_id")
        reason = request.POST.get("reason", "No reason specified.")
        booking = get_object_or_404(Booking, id=booking_id)

        try:
            booking.cancel()
            
            # Send Email to Customer
            from Reservations.services import send_booking_cancellation_email
            email_sent, error_msg = send_booking_cancellation_email(booking, cancelled_by='staff', reason=reason)
            
            if email_sent:
                messages.success(request, f"Booking cancelled. Email sent to {booking.customer.email}.")
            else:
                messages.warning(request, f"Booking cancelled, but email delivery failed: {error_msg}. Please notify the customer manually.")
        except Exception as e:
            messages.error(request, str(e))

    return redirect(request.META.get("HTTP_REFERER", "/"))


# -------------------------------
# Hide Review
# -------------------------------
@restrict_access
def hide(request):
    if request.method == "POST":
        review_id = request.POST.get("review_id")
        review = get_object_or_404(Review, id=review_id)

        review.hide_from_display()
        messages.success(request, "Review hidden from display.")

    return redirect(request.META.get("HTTP_REFERER", "/"))


# -------------------------------
# Unhide Review
# -------------------------------
@restrict_access
def unhide(request):
    if request.method == "POST":
        review_id = request.POST.get("review_id")
        review = get_object_or_404(Review, id=review_id)

        review.add_to_display()
        messages.success(request, "Review is now visible.")

    return redirect(request.META.get("HTTP_REFERER", "/"))


# --- Update Functions ---
@restrict_access
def updateBusiness(request, id):
    if request.method == "POST":
        instance = get_object_or_404(Restaurant, id=id)
        data = json.loads(request.body)
        perform_dynamic_update(instance, data)
        log_event(
            request.user.username,
            {
                "action": "updated_business",
                "details": f"Updated business {instance.name} (ID: {instance.id})",
            },
        )
        return JsonResponse({"status": "success", "message": "Business updated"})

@restrict_access
def updateTables(request, id):
    if request.method == "POST":
        instance = get_object_or_404(Table, id=id)
        data = json.loads(request.body)
        perform_dynamic_update(instance, data)
        log_event(
            request.user.username,
            {
                "action": "updated_table",
                "details": f"Updated table {instance.name} (ID: {instance.id}) in restaurant ID {instance.restaurant.id}",
            },
        )
        return JsonResponse({"status": "success", "message": "Table updated"})
    return redirect("/business/tables")

@restrict_access
def updateHolidays(request, id):
    if request.method == "POST":
        instance = get_object_or_404(SpecialDay, id=id)
        data = json.loads(request.body)
        perform_dynamic_update(instance, data)
        log_event(
            request.user.username,
            {
                "action": "updated_holiday",
                "details": f"Updated holiday {instance.name} (ID: {instance.id}) in restaurant ID {instance.restaurant.id}",
            },
        )
        return JsonResponse({"status": "success", "message": "Holiday updated"})


# --- Delete Functions ---
@restrict_access
def deleteBusiness(request, id):
    if request.method == "POST":
        instance = get_object_or_404(Restaurant, id=id)
        instance.delete()
        return redirect("/business/business-info/")


@restrict_access
def deleteTables(request, id):
    if request.method == "POST":
        instance = get_object_or_404(Table, id=id)
        instance.delete()
        return redirect("/business/tables/")


@restrict_access
def deleteHolidays(request, id):
    if request.method == "POST":
        instance = get_object_or_404(SpecialDay, id=id)
        instance.delete()
        return redirect("/business/holidays/")


@restrict_access
def download_logs(request):
    if not request.user.is_authenticated:
        return HttpResponse("Unauthorized", status=401)

    username = request.user.username

    logs = get_user_logs(username)
    formatted_text = format_logs_to_text(logs)

    response = HttpResponse(formatted_text, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{username}_logs.txt"'

    return response