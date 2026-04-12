from django.utils import timezone
from datetime import timedelta, datetime, time
from decimal import Decimal
from django.db import transaction
from django.shortcuts import get_object_or_404
from .utils import group_tables_by_seating
from django.utils.dateparse import parse_date, parse_time
from Restaurants.models import Table, SpecialDay, Restaurant
from .models import Booking  


LOCK_DURATION_MINUTES = 5


def check_special_day(restaurant, date):
    """
    Validate if restaurant is open on selected date.

    Raises:
        Exception if closed
    """
    special = SpecialDay.objects.filter(
        restaurant=restaurant,
        date=date
    ).first()

    if special and special.closed_full_day:
        raise Exception("Restaurant is closed on selected date")

    return special


def get_available_tables(restaurant, date, start_time, end_time):
    """
    Returns available tables excluding:
    - already booked tables
    - locked tables

    Lock logic:
        Any table locked within last 5 minutes is unavailable
    """
    now = timezone.now()

    # Combine date and times into awareness-ready datetimes for comparison
    start_dt = timezone.make_aware(datetime.combine(date, start_time))
    end_dt = timezone.make_aware(datetime.combine(date, end_time))

    booked_tables = Booking.objects.filter(
        restaurant=restaurant,
        booking_start_datetime__lt=end_dt,
        booking_end_datetime__gt=start_dt,
        status=Booking.STATUS_CONFIRMED
    ).values_list('tables__id', flat=True)

    locked_tables = Booking.objects.filter(
        status=Booking.STATUS_PENDING,
        locked_at__gte=now - timedelta(minutes=LOCK_DURATION_MINUTES)
    ).values_list('tables__id', flat=True)

    return Table.objects.filter(
        restaurant=restaurant,
        is_available=True
    ).exclude(id__in=booked_tables).exclude(id__in=locked_tables)


@transaction.atomic
def lock_tables(user, restaurant, tables, date, start_time, end_time):
    """
    Lock selected tables for 5 minutes.

    This prevents race conditions.

    Returns:
        booking instance (temporary)
    """
    now = timezone.now()

    # Re-check availability inside transaction (IMPORTANT)
    available_tables = get_available_tables(restaurant, date, start_time, end_time)
    available_ids = set(available_tables.values_list('id', flat=True))

    for table in tables:
        if table.id not in available_ids:
            raise Exception(f"Table {table.name} just got booked!")

    booking = Booking.objects.create(
        customer=user,
        restaurant=restaurant,
        booking_start_datetime=timezone.make_aware(datetime.combine(date, start_time)),
        booking_end_datetime=timezone.make_aware(datetime.combine(date, end_time)),
        locked_at=now,
        status=Booking.STATUS_PENDING
    )

    booking.tables.set(tables)
    return booking


def generate_time_slots(restaurant, interval_minutes=30):
    """
    Generate time slots within restaurant opening hours.
    
    Args:
        restaurant: Restaurant object with opening_time and closing_time
        interval_minutes: Time interval between slots (default 30 min)
    
    Returns:
        List of time strings in 'HH:MM' format
    """
    if not restaurant.opening_time or not restaurant.closing_time:
        # Default fallback if hours not set
        return [f"{h:02d}:{m:02d}" for h in range(11, 23) for m in (0, 30)]
    
    slots = []
    current = datetime.combine(datetime.today(), restaurant.opening_time)
    closing = datetime.combine(datetime.today(), restaurant.closing_time)
    
    # Handle overnight closing (e.g., 2 AM)
    if closing < current:
        closing += timedelta(days=1)
    
    while current <= closing:
        slots.append(current.strftime('%H:%M'))
        current += timedelta(minutes=interval_minutes)
    
    return slots


def validate_booking_time(restaurant, date, start_time, end_time):
    """
    Validate that booking time is within restaurant hours.
    
    Returns:
        (is_valid, error_message)
    """
    # Check if holiday
    special = SpecialDay.objects.filter(
        restaurant=restaurant,
        date=date,
        closed_full_day=True
    ).first()
    
    if special:
        return False, f"Restaurant is closed on {date} for {special.name}"
    
    # Check if within operating hours
    if start_time < restaurant.opening_time:
        return False, f"Booking starts before opening time ({restaurant.opening_time.strftime('%I:%M %p')})"
    
    if end_time > restaurant.closing_time:
        return False, f"Booking ends after closing time ({restaurant.closing_time.strftime('%I:%M %p')})"
    
    return True, None


def calculate_booking_price(tables, duration_hours):
    """
    Calculate total booking price.

    Includes:
    - table price
    - duration multiplier
    """
    total = 0

    for table in tables:
        table_price = table.calculate_price()
        total += table_price * duration_hours

    return total


def confirm_booking(booking):
    """
    Final confirmation of booking.

    After confirmation:
    - Lock removed
    - Booking becomes permanent
    """
    booking.status = Booking.STATUS_CONFIRMED
    booking.locked_at = None
    booking.save()

    return booking



def create_booking(request, Restaurant_name):
    # Fetch form data
    date_str = request.POST.get("date")  # 'YYYY-MM-DD'
    start_time_str = request.POST.get("start_time")  # 'HH:MM'
    try:
        duration_val = request.POST.get("duration", "0")
        if duration_val == "NaN" or not duration_val:
            duration_val = "1"
        duration = int(duration_val)
    except ValueError:
        duration = 1
    price = request.POST.get("price")
    table_ids = request.POST.getlist("table_ids")

    # Get restaurant object
    restaurant = get_object_or_404(Restaurant, name=Restaurant_name.replace("_", " "))

    # Combine date + time and make timezone-aware
    naive_start = datetime.strptime(f"{date_str.strip()} {start_time_str.strip()}", "%Y-%m-%d %H:%M")
    start_datetime = timezone.make_aware(naive_start, timezone.get_current_timezone())

    # Calculate end datetime - Ensuring duration is at least 1 hour if not specified
    if duration <= 0:
        duration = 1
    end_datetime = start_datetime + timedelta(hours=duration)

    # Create booking
    booking = Booking.objects.create(
        restaurant=restaurant,
        booking_start_datetime=start_datetime,
        booking_end_datetime=end_datetime,
        customer=request.user
    )

    # Set tables
    booking.tables.set(table_ids)

    # Calculate total price
    booking.total_price = sum(table.calculate_price() for table in booking.tables.all())
    booking.save()

    # Render checkout
    return  {
        "price": price,
        "name": restaurant.name,
        "start_time": start_time_str,
        "end_time": end_datetime.strftime("%H:%M"),
        "date": date_str,
        "tables": booking.tables.all()
    }


def mark_todays_booked_tables_unavailable(restaurant):
    """
    Fetches all of today's bookings for a given restaurant and marks
    all tables in those bookings as unavailable.
    
    Args:
        restaurant (Restaurant): Restaurant instance.
    
    Returns:
        int: Number of tables updated
    """

    # Get current timezone-aware now
    now = timezone.localtime(timezone.now())
    today_start = datetime.combine(now.date(), time.min)  # 00:00 today
    today_end = datetime.combine(now.date(), time.max)    # 23:59:59.999999 today

    # Make them timezone-aware if needed
    today_start = timezone.make_aware(today_start, timezone.get_current_timezone())
    today_end = timezone.make_aware(today_end, timezone.get_current_timezone())

    # Fetch today's bookings for this restaurant
    todays_bookings = Booking.objects.filter(
        restaurant=restaurant,
        booking_start_datetime__lte=today_end,
        booking_end_datetime__gte=today_start,
        status=Booking.STATUS_PENDING  # Only pending bookings occupy tables
    )

    # Collect all tables in these bookings
    tables_to_update = Table.objects.filter(bookings__in=todays_bookings).distinct()

    # Bulk update availability
    updated_count = tables_to_update.update(is_available=False)

    return updated_count



def view_all_booking(restaurant: Restaurant, date_str=None, start_time_str=None, end_time_str=None):
    """
    Fetch available tables for a restaurant, optionally filtering by date/time.
    
    Args:
        restaurant (Restaurant): Restaurant instance
        date_str (str, optional): 'YYYY-MM-DD'
        start_time_str (str, optional): 'HH:MM'
        end_time_str (str, optional): 'HH:MM'
    
    Returns:
        dict: Contains restaurant and tables data
    """

    # Reset availability and mark booked tables
    restaurant.tables.update(is_available=True)
    mark_todays_booked_tables_unavailable(restaurant)

    available_tables = restaurant.tables.filter(is_available=True)

    if date_str and start_time_str and end_time_str:
        # Parse strings into Python objects
        try:
            date = parse_date(date_str)
            start_time = parse_time(start_time_str)
            end_time = parse_time(end_time_str)

            # Check if restaurant is open on that date
            check_special_day(restaurant, date)

            # Filter tables that are available for the given date/time
            available_tables = get_available_tables(restaurant, date, start_time, end_time)

        except Exception as e:
            # Return empty tables and error for view to handle
            return {
                "restaurant": restaurant,
                "tables": {},
                "selected_date": date_str,
                "start_time": start_time_str,
                "end_time": end_time_str,
                "error": str(e)
            }

    # Group tables by seating type
    grouped = group_tables_by_seating(available_tables)
    tables_data = {
        key: [
            {"id": t.id, "name": t.name, "capacity": t.capacity, "price": float(t.calculate_price())}
            for t in value
        ]
        for key, value in grouped.items()
    }

    return {
        "restaurant": restaurant,
        "tables": tables_data,
        "selected_date": date_str,
        "start_time": start_time_str,
        "end_time": end_time_str
    }


def generate_invoice_html(booking):
    """
    Generate HTML invoice for booking.
    Dev-only: Creates printable HTML invoice (no PDF library needed)
    """
    from django.template.loader import render_to_string
    
    invoice_data = {
        'booking': booking,
        'restaurant': booking.restaurant,
        'customer': booking.customer,
        'tables': booking.tables.all(),
        'invoice_number': f"INV-{booking.id:06d}",
        'invoice_date': timezone.now().strftime('%Y-%m-%d'),
        'subtotal': booking.total_price,
        'tax': booking.total_price * Decimal('0.1'),  # 10% tax example
        'total': booking.total_price * Decimal('1.1'),
    }
    
    return render_to_string('Reservations/invoice_template.html', invoice_data)


def send_booking_confirmation_email(booking):
    """
    Send booking confirmation email to customer.
    Dev-only: Console backend for development (no SMTP needed)
    """
    from django.core.mail import send_mail
    from django.conf import settings
    
    subject = f'Booking Confirmation - {booking.restaurant.name}'
    message = f"""
    Dear {booking.customer.username},

    Your booking has been confirmed!

    Restaurant: {booking.restaurant.name}
    Date: {booking.booking_start_datetime.strftime('%B %d, %Y')}
    Time: {booking.booking_start_datetime.strftime('%I:%M %p')}
    Table(s): {', '.join([t.name for t in booking.tables.all()])}
    Total: ${booking.total_price}

    Booking Reference: #{booking.id}

    Thank you for choosing DineSphere!
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.customer.email],
            fail_silently=True,
        )
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False

def send_booking_cancellation_email(booking):
    """
    Simulates sending a cancellation and refund notification email to the customer.
    (Currently configured for console backend printing via settings).
    """
    subject = f"Order Cancelled: Reservation at {booking.restaurant.name}"
    
    # Message Body
    message = f"""
    Dear {booking.customer.username},

    Your reservation at {booking.restaurant.name} has been successfully cancelled.

    Reservation Details:
    Date: {booking.booking_start_datetime.strftime('%B %d, %Y')}
    Time: {booking.booking_start_datetime.strftime('%I:%M %p')}
    Table(s): {', '.join([t.name for t in booking.tables.all()])}
    
    Refund Status:
    Your payment of ${booking.total_price} has been marked for refund.
    Please allow 3-5 business days for the funds to appear on your statement.

    Cancelled Booking Reference: #{booking.id}

    We hope to host you another time!
    """
    
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@dinesphere.com'),
            recipient_list=[booking.customer.email],
            fail_silently=True,
        )
        return True
    except Exception as e:
        print(f"Cancellation Email sending failed: {e}")
        return False