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
from .models import Restaurant, Table, SpecialDay, Review, SeatingType, TableSize
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
        # Extract fields for repopulation
        res_name = request.POST.get("res_name", "").strip()
        res_title = request.POST.get("res_title", "").strip()
        res_about = request.POST.get("res_about", "")
        city = request.POST.get("city", "").strip()
        address = request.POST.get("address", "").strip()
        phone = request.POST.get("phone", "").strip()
        open_hour = request.POST.get("open_hour", "18:00")
        close_hour = request.POST.get("close_hour", "01:00")
        cooldown = request.POST.get("cooldown", "30")
        slot_duration = request.POST.get("slot_duration", "60")
        advance_days = request.POST.get("advance_days", "60")
        fb_link = request.POST.get("fb_link", "")
        web_link = request.POST.get("web_link", "")

        try:
            # Parse times safely
            try:
                opening_time = datetime.strptime(open_hour, "%H:%M").time()
                closing_time = datetime.strptime(close_hour, "%H:%M").time()
            except ValueError:
                raise ValueError("Invalid time format. Please use HH:MM.")

            data = {
                "name": res_name,
                "title": res_title or res_name,
                "image": request.FILES.get("res_image"),
                "about": res_about,
                "city": city,
                "address": address,
                "phone": phone,
                "opening_hour": opening_time,
                "closing_hour": closing_time,
                "cooldown": int(cooldown or 30),
                "slot_duration": int(slot_duration or 60),
                "advance_days": int(advance_days or 60),
                "fb_link": fb_link,
                "web_link": web_link,
            }

            if not data["name"]:
                raise ValueError("Restaurant name is required.")
            if not data["city"]:
                raise ValueError("City is required.")

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
            # Fall through to render with context
            
    # GET or POST-error
    seating_types = SeatingType.objects.all()
    context = {
        "seatingtype": seating_types,
        # Pass back all form data for repopulation
        "res_name": request.POST.get("res_name", ""),
        "res_title": request.POST.get("res_title", ""),
        "res_about": request.POST.get("res_about", ""),
        "city": request.POST.get("city", ""),
        "address": request.POST.get("address", ""),
        "phone": request.POST.get("phone", ""),
        "open_hour": request.POST.get("open_hour", "18:00"),
        "close_hour": request.POST.get("close_hour", "01:00"),
        "cooldown": request.POST.get("cooldown", "30"),
        "slot_duration": request.POST.get("slot_duration", "60"),
        "advance_days": request.POST.get("advance_days", "60"),
        "fb_link": request.POST.get("fb_link", ""),
        "web_link": request.POST.get("web_link", ""),
    }
    
    return render(request, "Restaurants/registration.html", context)




@restrict_access
def staff_management(request):
    # 1. Get the current restaurant ID from the session
    restaurant_id = request.session.get("selected_restaurant_id")

    if isStaff(request.user):
        staff = RestaurantStaff.objects.filter(user=request.user).first()
        if staff:
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
        restaurant_id = request.session.get("selected_restaurant_id")
        restaurant = get_object_or_404(Restaurant, id=restaurant_id) if restaurant_id else None
        
        if active_tab:
            # 2. Bind the POST data to the specific form class
            form = getForm(active_tab, data=request.POST, restaurant=restaurant)
            
            # 3. Validate and Save
            if form and form.is_valid():
                obj = form.save(commit=False)
                if restaurant and hasattr(obj, 'restaurant') and obj.restaurant is None:
                    obj.restaurant = restaurant
                obj.save()
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
            context["form"] = getForm(tab, restaurant=get_object_or_404(Restaurant, id=restaurant_id) if restaurant_id else None)
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
        from django.db.models import Q
        seating_types = SeatingType.objects.filter(Q(restaurant__isnull=True) | Q(restaurant=restaurant))
        table_sizes = TableSize.objects.filter(Q(restaurant__isnull=True) | Q(restaurant=restaurant))
        return render(request, "Restaurants/tables.html", {
            "form": form,
            "seating_types": seating_types,
            "table_sizes": table_sizes
        })
    elif request.method == "POST":
        form, success = add_table(request, restaurant_id)
        if success:
            log_event(
                request.user.username,
                {
                    "action": "added_table",
                    "details": f"Added table to restaurant ID {restaurant_id}",
                }
            )
            messages.success(request, "Table added successfully!")
            return redirect("/business/tables/")
        else:
            messages.error(request, "Failed to add table. Please check the form for errors.")
            from django.db.models import Q
            seating_types = SeatingType.objects.filter(Q(restaurant__isnull=True) | Q(restaurant=restaurant))
            table_sizes = TableSize.objects.filter(Q(restaurant__isnull=True) | Q(restaurant=restaurant))
            return render(request, "Restaurants/tables.html", {"form": form, "seating_types": seating_types, "table_sizes": table_sizes})


@restrict_access
def holidays(request):
    restaurant_id = request.session.get("selected_restaurant_id")
    if not restaurant_id:
        return redirect("/business/registration/")
    restaurant = get_object_or_404(Restaurant, id=id) if 'id' in locals() else get_object_or_404(Restaurant, id=restaurant_id)

    from .forms import SpecialDayForm, WeeklyScheduleForm
    from .models import SpecialDay, WeeklySchedule

    if request.method == "GET":
        holiday_form = SpecialDayForm()
        weekly_form = WeeklyScheduleForm()
        
        special_days = SpecialDay.objects.filter(restaurant=restaurant)
        
        # Prepare data for the 7 days
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        db_schedules = {s.day_of_week: s for s in WeeklySchedule.objects.filter(restaurant=restaurant)}
        
        weekly_data = []
        for i, name in enumerate(day_names):
            weekly_data.append({
                'day_idx': i,
                'day_name': name,
                'schedule': db_schedules.get(i)
            })

        return render(
            request,
            "Restaurants/holidays.html",
            {
                "form": holiday_form, 
                "weekly_form": weekly_form,
                "special_days": special_days,
                "weekly_data": weekly_data,
                "restaurant": restaurant,
            },
        )

    elif request.method == "POST":
        action = request.POST.get('action')
        
        if action == 'add_weekly':
            form = WeeklyScheduleForm(request.POST)
            if form.is_valid():
                day_of_week = form.cleaned_data['day_of_week']
                # Update or create
                WeeklySchedule.objects.update_or_create(
                    restaurant=restaurant,
                    day_of_week=day_of_week,
                    defaults={
                        'is_closed': form.cleaned_data['is_closed'],
                        'opening_hour': form.cleaned_data.get('opening_hour'),
                        'closing_hour': form.cleaned_data.get('closing_hour'),
                    }
                )
                day_name = dict(WeeklySchedule.DAYS_OF_WEEK).get(int(day_of_week), "Selected Day")
                messages.success(request, f"Weekly schedule updated for {day_name}s.")
            else:
                messages.error(request, "Failed to update weekly schedule.")
                
        else:
            # Default to original holiday logic
            form = SpecialDayForm(request.POST)
            if form.is_valid():
                instance = form.save(commit=False)
                instance.restaurant = restaurant
                instance.save()
                messages.success(request, "Special holiday added successfully.")
            else:
                messages.error(request, "Failed to add holiday.")

        return redirect("/business/holidays/")

@restrict_access
def reviews(request):
    restaurant_id = request.session.get("selected_restaurant_id")
    restaurant = Restaurant.objects.filter(id=restaurant_id).first()

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
            log_event(
                request.user.username,
                {
                    "action": "added_review",
                    "details": f"Added review to restaurant {reviews.comment} by {reviews.user})",
                },
            )   
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
    # Exclude unpaid abandoned checkouts so they don't show on the dashboard
    reservations_query = Booking.objects.filter(
        restaurant=restaurant
    ).exclude(
        status=Booking.STATUS_PENDING,
        payment_status=Booking.PAYMENT_STATUS_PENDING
    )
    
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
        try:
            instance = get_object_or_404(Restaurant, id=id)
            
            # Determine content type
            content_type = request.content_type or ''
            
            if 'application/json' in content_type:
                data = json.loads(request.body)
            else:
                # Handle FormData (multipart/form-data)
                data = {}
                for key in request.POST:
                    if key == 'csrfmiddlewaretoken':
                        continue
                    values = request.POST.getlist(key)
                    data[key] = values if len(values) > 1 else values[0]
                
                # Directly handle files
                if request.FILES:
                    for key, file in request.FILES.items():
                        setattr(instance, key, file)
            
            # Update other fields
            perform_dynamic_update(instance, data)
            
            log_event(
                request.user.username,
                {
                    "action": "updated_business",
                    "details": f"Updated business {instance.name} (ID: {instance.id})",
                },
            )
            return JsonResponse({"status": "success", "message": "Business updated"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

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
def deleteSeatingType(request, id):
    if request.method == "POST":
        instance = get_object_or_404(SeatingType, id=id)
        # Protect global defaults — only custom (restaurant-specific) types can be deleted
        if instance.restaurant is None:
            return JsonResponse({"status": "error", "message": "Cannot delete a global default seating type."}, status=403)
        instance.delete()
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)


@restrict_access
def deleteTableSize(request, id):
    if request.method == "POST":
        instance = get_object_or_404(TableSize, id=id)
        # Protect global defaults — only custom (restaurant-specific) sizes can be deleted
        if instance.restaurant is None:
            return JsonResponse({"status": "error", "message": "Cannot delete a global default table size."}, status=403)
        instance.delete()
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)


@restrict_access
def download_logs(request):
    if not request.user.is_authenticated:
        return HttpResponse("Unauthorized", status=401)

    username = request.user.username
    logs = get_user_logs(username)

    # User Request: Add test entries if none exist
    if not logs:
        log_event(
            username, 
            {
                "action": "system_check",
                "details": "MongoDB logging flow verified. This entry created automatically for testing.",
                "status": "connected"
            }
        )
        logs = get_user_logs(username)

    formatted_text = format_logs_to_text(logs)
    response = HttpResponse(formatted_text, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{username}_activity_logs.txt"'
    return response


def get_operational_hours(request):
    """
    AJAX endpoint to get restaurant hours for a specific date.
    Accounts for SpecialDay and WeeklySchedule.
    """
    from Reservations.services import check_special_day
    from django.utils.dateparse import parse_date
    from .models import Restaurant
    from django.http import JsonResponse
    from django.shortcuts import get_object_or_404
    
    restaurant_id = request.GET.get('restaurant_id')
    date_str = request.GET.get('date')
    
    if not restaurant_id or not date_str:
        return JsonResponse({'error': 'Missing parameters'}, status=400)
        
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    date = parse_date(date_str)
    
    try:
        schedule = check_special_day(restaurant, date)
        
        # Determine hours
        opening = restaurant.opening_hour
        closing = restaurant.closing_hour
        
        if schedule:
            if hasattr(schedule, 'adjusted_opening_hour'): # It's a SpecialDay
                if schedule.adjusted_opening_hour:
                    opening = schedule.adjusted_opening_hour
                if schedule.adjusted_closing_hour:
                    closing = schedule.adjusted_closing_hour
            else: # It's a WeeklySchedule
                if schedule.opening_hour:
                    opening = schedule.opening_hour
                if schedule.closing_hour:
                    closing = schedule.closing_hour
                
        return JsonResponse({
            'status': 'open',
            'opening': opening.strftime('%H:%M'),
            'closing': closing.strftime('%H:%M'),
            'opening_display': opening.strftime('%I:%M %p'),
            'closing_display': closing.strftime('%I:%M %p')
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'closed',
            'message': str(e)
        })