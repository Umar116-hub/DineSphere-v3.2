from .models import Restaurant, ReviewSummary, TableSize, SeatingType
from UsersHandling.models import RestaurantStaff, User
from django.db.models import ForeignKey, ManyToManyField, BooleanField, FileField, IntegerField, Count
from Reservations.models import Booking
from django.db.models import Sum, Count, Q


from .forms import *
def create_restaurant(data):
    restaurant = Restaurant.objects.create(
        name=data["name"],
        title=data["title"],
        image=data.get("image"),
        about_restaurant=data.get("about"),
        city=data["city"],
        address=data.get("address", "Earth - The only known habitable planet"),
        phone_number=data.get("phone"),
        cool_down=data.get("cooldown", 30),
        default_opening_hour=data["opening_hour"],
        default_closing_hour=data["closing_hour"],
        slot_duration_minutes=data.get("slot_duration", 60),
        allow_advance_booking_days=data.get("advance_days", 30),
        fb_link=data.get("fb_link"),
        website_link=data.get("web_link"),
        is_approved=False
    )

    # Create review summary
    ReviewSummary.objects.create(restaurant=restaurant)

    # ManyToMany seating types
    if data.get("seating_types"):
        restaurant.seating_types.set(data["seating_types"])

    return restaurant



def create_restaurant_for_user(user, data):
    # Step 1: Strict Check - only existing Owners can register restaurants
    if user.role != 'OWNER':
        raise ValueError("Only dedicated Owner accounts can register restaurants. Please create an Owner account.")

    # Step 2: Create restaurant
    restaurant = create_restaurant(data)

    # Step 3: Assign ownership
    RestaurantStaff.objects.create(
        user=user,
        restaurant=restaurant,
        role="OWNER"
    )

    return restaurant


"""Services that are called from business dashboard direclty"""

# -------------------------------
# Add Table
# -------------------------------
def add_table(request, restaurant_id):
    restaurant = Restaurant.objects.get(id=restaurant_id)

    if request.method == 'POST':
        form = TableForm(request.POST, restaurant=restaurant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.restaurant = restaurant
            obj.save()
    else:
        form = TableForm(restaurant=restaurant)

    return form, form.is_bound and form.is_valid()


# -------------------------------
# Add Table Size (TableType)
# -------------------------------
def add_tabletype(request, restaurant=None):
    # restaurant not needed, but kept for consistency

    if request.method == 'POST':
        form = TableSizeForm(request.POST)
        if form.is_valid():
            form.save()
    else:
        form = TableSizeForm()

    return form, form.is_bound and form.is_valid()


# -------------------------------
# Add Seating Type (optional but useful)
# -------------------------------
def add_seating_type(request, restaurant=None):
    if request.method == 'POST':
        form = SeatingTypeForm(request.POST)
        if form.is_valid():
            form.save()
    else:
        form = SeatingTypeForm()

    return form, form.is_bound and form.is_valid()


# -------------------------------
# Add Holiday / Special Day
# -------------------------------
def add_holiday(request, restaurant):
    if request.method == 'POST':
        form = SpecialDayForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.restaurant = restaurant
            obj.save()
    else:
        form = SpecialDayForm()

    return form, form.is_bound and form.is_valid()


# -------------------------------
# Add Restaurant
# -------------------------------
def add_restaurant(request, restaurant=None):
    # restaurant param unused, just for consistent signature

    if request.method == 'POST':
        form = RestaurantForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
    else:
        form = RestaurantForm()

    return form, form.is_bound and form.is_valid()



def perform_dynamic_update(instance, data):
    field_dict = {f.name: f for f in instance._meta.get_fields() if not f.auto_created}
    
    for key, value in data.items():
        if key == 'id' or key not in field_dict:
            continue
            
        field = field_dict[key]

        # ❌ NEW: Skip Image/File fields in JSON updates
        # JSON cannot send files; it only sends the path/filename as a string.
        # Assigning a string to an ImageField breaks Django's save() method.
        if isinstance(field, FileField):
            continue

        if isinstance(field, IntegerField):
            if value in ['', 'None', None]:
                value = None

        # 1. Many-to-Many
        if isinstance(field, ManyToManyField):
            if isinstance(value, list):
                getattr(instance, key).set(value)
            elif isinstance(value, str):
                ids = [v.strip() for v in value.split(',') if v.strip()]
                getattr(instance, key).set(ids)
            continue 

        # 2. Foreign Keys
        if isinstance(field, ForeignKey) and value:
            related_model = field.remote_field.model
            try:
                value = related_model.objects.get(id=value)
            except (related_model.DoesNotExist, ValueError):
                continue

        # 3. Booleans
        if isinstance(field, BooleanField):
            value = str(value).lower() in ['true', 'on', '1', 'yes']

        # 4. Standard Assignment (only if value isn't empty for numeric fields)
        if value is not None:
            setattr(instance, key, value)
    
    instance.save()
    return instance



def getAnalytics(restaurant_id):
    """
    Calculate real restaurant analytics from booking data.
    Replaces fake static values with actual database queries.
    """
    from django.utils import timezone
    from datetime import timedelta
    
    # Get bookings that count towards operations: exclude unpaid/abandoned checkouts
    valid_bookings = Booking.objects.filter(
        restaurant_id=restaurant_id
    ).exclude(
        status=Booking.STATUS_PENDING,
        payment_status=Booking.PAYMENT_STATUS_PENDING
    )
    
    # Deduct Cancelled implicitly by not including them for revenue.
    revenue_bookings = valid_bookings.exclude(status=Booking.STATUS_CANCELLED)
    
    # Real booking statistics (all non-cancelled)
    total_bookings = revenue_bookings.count()
    
    # Real revenue
    total_revenue = revenue_bookings.aggregate(
        total=Sum('total_price')
    )['total'] or 0
    
    # This week's bookings
    week_ago = timezone.now() - timedelta(days=7)
    this_week_bookings = revenue_bookings.filter(
        created_at__gte=week_ago
    ).count()
    
    # Last week's bookings for comparison
    two_weeks_ago = timezone.now() - timedelta(days=14)
    last_week_bookings = revenue_bookings.filter(
        created_at__gte=two_weeks_ago,
        created_at__lt=week_ago
    ).count()
    
    # Calculate weekly growth percentage
    if last_week_bookings > 0:
        weekly_growth = ((this_week_bookings - last_week_bookings) / last_week_bookings) * 100
    else:
        weekly_growth = 0 if this_week_bookings == 0 else 100
    
    # Upcoming bookings (today and future)
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    upcoming_bookings = revenue_bookings.filter(
        booking_start_datetime__gte=today
    ).count()
    
    # Average party size - calculated in Python because guest_count is a property
    # We take all confirmed bookings and average their guest_count property
    all_guest_counts = [b.guest_count for b in revenue_bookings]
    avg_guests = sum(all_guest_counts) / len(all_guest_counts) if all_guest_counts else 0
    
    # Real staff count
    staff_count = RestaurantStaff.objects.filter(
        restaurant_id=restaurant_id
    ).count()
    
    # Order status breakdown
    order_stats = valid_bookings.aggregate(
        pending_count=Count('id', filter=Q(status=Booking.STATUS_PENDING)),
        confirmed_count=Count('id', filter=Q(status=Booking.STATUS_CONFIRMED)),
        approved_count=Count('id', filter=Q(status=Booking.STATUS_FINISHED)),
        cancelled_count=Count('id', filter=Q(status=Booking.STATUS_CANCELLED)),
        total_bookings=Count('id')
    )
    
    return {
        'total_bookings': total_bookings,
        'total_revenue': total_revenue,
        'this_week_bookings': this_week_bookings,
        'last_week_bookings': last_week_bookings,
        'weekly_growth': round(weekly_growth, 1),
        'upcoming_bookings': upcoming_bookings,
        'avg_guests': round(avg_guests, 1),
        'staff_count': staff_count,
        'stats': order_stats,
        # Remove fake demographics - use real data only
        'total_customers': revenue_bookings.values('customer').distinct().count(),
    }


def auto_approve_bookings(restaurant_id):
    """
    Finds and approves all pending bookings older than 12 hours.
    Used for the 'Auto-Approve' feature.
    """
    from django.utils import timezone
    from datetime import timedelta
    
    limit = timezone.now() - timedelta(hours=12)
    
    pending_to_approve = Booking.objects.filter(
        restaurant_id=restaurant_id,
        status=Booking.STATUS_PENDING,
        created_at__lte=limit
    )
    
    approved_count = 0
    for booking in pending_to_approve:
        if booking.approve():
            approved_count += 1
            
    return approved_count


def isStaff(user):
    return RestaurantStaff.objects.filter(
        user=user,
        role="STAFF"
    ).exists()

def isOwner(user):
    return RestaurantStaff.objects.filter(
        user=user,
        role="OWNER"
    ).exists()


def getForm(tab:str, data=None):

    match tab.lower():
        case "seatingtype":
            return SeatingTypeForm(data=data)
        case "tablesize":
            return TableSizeForm(data=data)
        case _:
            raise ValueError("Invalid tab name")
        


from django.http import JsonResponse

def get_items(request):
    item_type = request.GET.get('type', '').lower()
    items = []

    try:
        if item_type == 'seatingtype':
            data = SeatingType.objects.all()
            # SeatingType only has 'name'
            items = [{'primary': obj.name, 'secondary': 'Area Type'} for obj in data]
            
        elif item_type == 'tablesize':
            data = TableSize.objects.all()
            # TableSize has 'size' and 'capacity'
            items = [
                {
                    'primary': f"{obj.size}" if obj.size else "Standard", 
                    'secondary': f"{obj.capacity} Seats"
                } for obj in data
            ]

        return JsonResponse({'items': items})
    except Exception as e:
        return JsonResponse({'items': [], 'error': str(e)}, status=400)