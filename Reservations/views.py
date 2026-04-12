from datetime import datetime, timedelta
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.db import transaction
from .models import Booking
from Restaurants.models import Restaurant, Table, Review
from .services import view_all_booking, create_booking, generate_invoice_html, send_booking_confirmation_email, send_booking_cancellation_email

def booking_view(request, Restaurant_name):
    """
    Handles restaurant table reservations.

    GET: Display only available tables for the selected date and time.
    POST: Submit the booking form (simpler, just submits data).

    GET parameters (optional):
        - date
        - start_time
        - end_time

    POST parameters:
        - date, start_time, end_time, table_ids, required_capacity
    """
    Restaurant_name = Restaurant_name.replace("_", " ")
    restaurant = get_object_or_404(Restaurant, name=Restaurant_name)

    if request.method == "GET":
        # Call service function to get tables
        booking_data = view_all_booking(
            restaurant,
            date_str=request.GET.get("date"),
            start_time_str=request.GET.get("start_time"),
            end_time_str=request.GET.get("end_time")
        )
        booking_data['reviews'] = Review.objects.filter(restaurant=restaurant)
        return render(request, "Reservations/reservation.html", booking_data)

    elif request.method == "POST":
        context = create_booking(request, Restaurant_name)
        return render(request, "Reservations/checkout.html", context)



@login_required
def checkout_view(request):
    if request.method == "POST":
        return placeOrder_view(request)
        
    # Safely reconstruct the checkout context from the pending booking if returning via GET
    booking = Booking.objects.filter(
        customer=request.user,
        status=Booking.STATUS_PENDING
    ).order_by('-created_at').first()
    
    if not booking:
        messages.error(request, "No pending booking found to checkout.")
        return redirect("home")
        
    context = {
        "price": f"${booking.total_price:.2f}",
        "name": booking.restaurant.name,
        "start_time": booking.booking_start_datetime.strftime("%H:%M"),
        "end_time": booking.booking_end_datetime.strftime("%H:%M"),
        "date": booking.booking_start_datetime.strftime("%Y-%m-%d"),
        "tables": booking.tables.all()
    }
    
    return render(request, "Reservations/checkout.html", context)



@login_required
@transaction.atomic
def placeOrder_view(request):
    """
    Process payment and confirm booking.
    Uses atomic transaction with select_for_update to prevent race conditions.
    """
    s_time = request.POST.get("s_time")
    date = request.POST.get("date")
    
    if not s_time or not date:
        messages.error(request, "Missing booking information.")
        return redirect("checkout")
    
    # Get the latest pending booking for this user
    # The booking was created when user clicked "Reserve & Lock" on reservation page
    booking = Booking.objects.select_for_update().filter(
        customer=request.user,
        status=Booking.STATUS_PENDING
    ).order_by('-created_at').first()
    
    if not booking:
        messages.error(request, "No pending booking found. Please create a booking first.")
        return redirect("home")
    
    # Get tables associated with this booking
    tables = list(booking.tables.all())
    
    if not tables:
        messages.error(request, "No tables selected for this booking.")
        return redirect("home")
    
    # Verify tables are still available (double-check inside transaction)
    for table in tables:
        overlapping = Booking.objects.filter(
            tables=table,
            status=Booking.STATUS_CONFIRMED,
            booking_start_datetime__lt=booking.booking_end_datetime,
            booking_end_datetime__gt=booking.booking_start_datetime
        ).exclude(id=booking.id).exists()
        
        if overlapping:
            messages.error(request, f"Table {table.name} is no longer available. Please select different tables.")
            booking.delete()
            return redirect("home")
    
    # Process payment (mock validation)
    card_number = request.POST.get("cn", "").replace(" ", "")
    if len(card_number) < 13 or not card_number.isdigit():
        messages.error(request, "Please enter a valid card number.")
        return redirect("checkout")
    
    # Confirm the booking
    booking.status = Booking.STATUS_CONFIRMED
    booking.payment_status = Booking.PAYMENT_STATUS_PAID
    booking.save()
    
    # Send confirmation email
    send_booking_confirmation_email(booking)
    
    messages.success(request, "Booking confirmed successfully!")
    return redirect("order_success", booking_id=booking.id)
        
    # We no longer broadly catch Exception here. 
    # If a generic server or code logic error occurs, it should 500 loudly 
    # so we can track and fix it, rather than silently redirecting.


@login_required
def order_success(request, booking_id):
    """Display booking confirmation with invoice option."""
    booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
    
    # Generate invoice HTML
    invoice_html = generate_invoice_html(booking)
    
    return render(request, "Reservations/success.html", {
        "booking": booking,
        "invoice_html": invoice_html,
        "restaurant": booking.restaurant
    })


@login_required
def view_invoice(request, booking_id):
    """Display printable invoice for a booking."""
    booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
    
    invoice_html = generate_invoice_html(booking)
    
    return HttpResponse(invoice_html)


@login_required
def post_review(request, Restaurant_name):
    if request.method == "POST":
        rating = request.POST.get("rating")
        text = request.POST.get("text")
        # Validate data
        if not rating:
            return JsonResponse({"success": False, "error": "Rating required"})
        
        # Save review to your model
        restaurant = get_object_or_404(Restaurant, name=Restaurant_name.replace("_", " "))
        Review.objects.create(
            restaurant=restaurant,
            user=request.user,
            rating=rating,
            comment=text,
            on_display=False
        )

        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "error": "Invalid request method"})


from django.utils.dateparse import parse_date

def get_unavailable_tables(request):
    restaurant_name = request.GET.get("restaurant")
    date_str = request.GET.get("date")

    if not restaurant_name or not date_str:
        return JsonResponse({"error": "Missing params"}, status=400)

    restaurant = get_object_or_404(Restaurant, name=restaurant_name.replace("_", " "))
    selected_date = parse_date(date_str)

    # Get bookings for that restaurant + date
    bookings = Booking.objects.filter(
        restaurant=restaurant,
        booking_start_datetime__date=selected_date,
        status=Booking.STATUS_PENDING
    ).prefetch_related('tables')

    # Collect booked table IDs
    booked_table_ids = set()
    for booking in bookings:
        for table in booking.tables.all():
            booked_table_ids.add(table.id)

    return JsonResponse({
        "booked_tables": list(booked_table_ids)
    })

@login_required
@transaction.atomic
def cancel_booking_view(request, booking_id):
    """
    Cancels a confirmed order and simulates a refund if it is requested
    more than 2 hours before the scheduled reservation start time.
    """
    booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
    
    # Must be pending or confirmed to cancel online. 
    # (Pending means they just created it but didn't pay in checkout).
    if booking.status not in [Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED]:
        messages.error(request, 'This booking cannot be cancelled.')
        return redirect('profile')

    # Enforce 2-hour cutoff rule if the booking is already confirmed (paid)
    if booking.status == Booking.STATUS_CONFIRMED:
        time_until_start = booking.booking_start_datetime - timezone.now()
        if time_until_start < timedelta(hours=2):
            messages.error(request, 'Too late to cancel online. Please call the restaurant directly.')
            return redirect('profile')

    # Apply Cancellation and Refund Logic
    booking.status = Booking.STATUS_CANCELLED
    if booking.payment_status == Booking.PAYMENT_STATUS_PAID:
        booking.payment_status = Booking.PAYMENT_STATUS_REFUNDED
    booking.save()
    
    # Fire refund email mock if they actually paid
    if booking.payment_status == Booking.PAYMENT_STATUS_REFUNDED:
        send_booking_cancellation_email(booking)

    messages.success(request, f'Order #{booking.id} has been cancelled successfully.')
    return redirect('profile')