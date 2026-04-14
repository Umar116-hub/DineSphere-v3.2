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
from .services import (
    view_all_booking, create_booking, generate_invoice_html,
    send_booking_confirmation_email, send_booking_cancellation_email,
    notify_owner_of_cancellation
)
from Core.decorators import customer_required

@customer_required
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
        try:
            context = create_booking(request, Restaurant_name)
            return render(request, "Reservations/checkout.html", context)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect("booking", Restaurant_name=Restaurant_name.replace(" ", "_"))



@customer_required
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
        "tables": booking.tables.all(),
        "restaurant_image": booking.restaurant.image.url if booking.restaurant.image else None
    }
    
    return render(request, "Reservations/checkout.html", context)



@customer_required
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
    booking = Booking.objects.select_for_update().filter(
        customer=request.user,
        status=Booking.STATUS_PENDING
    ).order_by('-created_at').first()
    
    if not booking:
        messages.error(request, "Your booking session has expired. Please try reserving again.")
        return redirect("home")
    
    # Get tables associated with this booking
    tables = list(booking.tables.all())
    
    if not tables:
        messages.error(request, "It looks like no tables were selected. Please try the reservation process again.")
        return redirect("checkout")
    
    # Process payment (mock validation)
    card_number = request.POST.get("cn", "").replace(" ", "")
    if len(card_number) < 13 or not card_number.isdigit():
        messages.error(request, "Please enter a valid card number.")
        return redirect("checkout")
    
    # Update payment status but keep reservation status as PENDING (as per new 12h rule)
    # The status is already pending from the initial booking creation.
    booking.payment_status = Booking.PAYMENT_STATUS_PAID
    booking.save()
    
    # Send confirmation email
    send_booking_confirmation_email(booking)
    
    messages.success(request, "Booking confirmed successfully!")
    return redirect("order_success", booking_id=booking.id)


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
        review = Review.objects.create(
            restaurant=restaurant,
            user=request.user,
            rating=rating,
            comment=text,
            on_display=False  # Hidden by default for moderation
        )

        # Update ReviewSummary
        from Restaurants.models import ReviewSummary
        summary, created = ReviewSummary.objects.get_or_create(restaurant=restaurant)
        rating_int = int(rating)
        if rating_int == 5: summary.five_star += 1
        elif rating_int == 4: summary.four_star += 1
        elif rating_int == 3: summary.three_star += 1
        elif rating_int == 2: summary.two_star += 1
        elif rating_int == 1: summary.one_star += 1
        summary.save()

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

    # Filter: Enforce 12-hour cancellation rule
    if not booking.can_cancel:
        messages.error(request, 'The 12-hour cancellation window for this booking has expired.')
        return redirect('profile')

    # Apply Cancellation and Refund Logic
    booking.status = Booking.STATUS_CANCELLED
    if booking.payment_status == Booking.PAYMENT_STATUS_PAID:
        booking.payment_status = Booking.PAYMENT_STATUS_REFUNDED
    booking.save()
    
    # Send customer cancellation email
    send_booking_cancellation_email(booking)
    
    # Notify the restaurant owner
    notify_owner_of_cancellation(booking)

    if booking.payment_status == Booking.PAYMENT_STATUS_REFUNDED:
        messages.success(
            request,
            f'Booking #{booking.id} at {booking.restaurant.name} has been cancelled. '
            f'A refund of ${booking.total_price} is being processed — please check your email for details.'
        )
    else:
        messages.success(request, f'Booking #{booking.id} has been cancelled successfully.')
    
    return redirect('profile')