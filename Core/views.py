from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from Restaurants.models import Restaurant, FavouriteRestaurant
from Reservations.models import Booking
from UsersHandling.models import CustomerProfile
from django.db import models
from django.db.models import Q
from .utils import build_combined



# Create your views here.
def home_page(request):
    restaurants = Restaurant.objects.filter(is_approved=True)
    three_users = CustomerProfile.objects.all()[:3]
    favorite_restaurants = []
    user_image = None

    if request.user.is_authenticated:
        user_favs = FavouriteRestaurant.objects.filter(user=request.user).values_list('restaurant_id', flat=True)


        # adding temporary is_favourite attribute to each restaurant
        restaurants = restaurants.annotate(
            is_favourite=models.Case(
                models.When(id__in=user_favs, then=models.Value(True)),
                default=models.Value(False),
                output_field=models.BooleanField()
            )
        )
        # Get only favorite restaurants for the favorites carousel
        favorite_restaurants = Restaurant.objects.filter(id__in=user_favs, is_approved=True).annotate(
            is_favourite=models.Value(True, output_field=models.BooleanField())
        )
        if request.user.image:
            user_image = request.user.image.url


    # Build combined dataset for all restaurants containing restaurant details, review summaries, and minimum prices
    combined = build_combined(restaurants) 

    # Build combined dataset for all favorite restaurants containing restaurant details, review summaries, and minimum prices
    favorite_combined = build_combined(favorite_restaurants)

    return render(request, "Core/home.html", {
        "Restaurants": restaurants,
        "combined":combined,
        "user_image": user_image if request.user.is_authenticated else None,
        "favorite_combined": favorite_combined,
        "footer": True,
        "three_users": three_users 
    })


def profile(request):
    if not request.user.is_authenticated:
        return redirect("../uh/auth")

    user_profile = CustomerProfile.objects.filter(user=request.user).first()
    bookings = Booking.objects.filter(customer=request.user).order_by('-created_at')
    completed_booking = bookings.filter(status=Booking.STATUS_FINISHED)
    pending_booking = bookings.filter(status=Booking.STATUS_PENDING)
    canceled_booking = bookings.filter(status=Booking.STATUS_CANCELLED)
    return render(request, "Core/Profile.html", {
        "user_profile": user_profile,
        "footer":False,
        "completed_booking": completed_booking if len(completed_booking) > 0 else None,
        "pending_booking": pending_booking if len(pending_booking) > 0 else None,
        "canceled_booking": canceled_booking if len(canceled_booking) > 0 else None,
    })

@login_required
def toggle_favourite(request):
    if request.method == "POST":
        restaurant_id = request.POST.get("restaurant_id")
        user = request.user

        restaurant_instance = get_object_or_404(Restaurant, id=restaurant_id)

        fav_instance = FavouriteRestaurant.objects.filter(user=user, restaurant=restaurant_instance)

        if fav_instance.exists():
            fav_instance.delete()
            favourited = False
        else:
            FavouriteRestaurant.objects.create(user=user, restaurant=restaurant_instance)
            favourited = True

        return JsonResponse({"success": True, "favourited": favourited})

    return JsonResponse({"success": False, "error": "Invalid request method"})


# from django.shortcuts import render

def search(request):
    query = (request.GET.get("searched-restaurant") or "").strip()
    city = (request.GET.get("city") or "").strip()

    restaurants = Restaurant.objects.filter(is_approved=True)


    if city:
        restaurants = restaurants.filter(city__iexact=city)

    if query:
        words = query.split()

        for word in words:
            restaurants = restaurants.filter(
                Q(name__icontains=word) |
                Q(title__icontains=word) |
                Q(about_restaurant__icontains=word)
            )

    restaurants = restaurants.distinct()
    total = restaurants.count()
    if request.user.is_authenticated:
        user_favs = FavouriteRestaurant.objects.filter(user=request.user).values_list('restaurant_id', flat=True)
        restaurants = restaurants.annotate(
                is_favourite=models.Case(
                    models.When(id__in=user_favs, then=models.Value(True)),
                    default=models.Value(False),
                    output_field=models.BooleanField()
                )
            )
        
    combined = build_combined(restaurants)

    return render(request, "Core/home.html", {
        "results": combined,
        "count": total,
        "query": query,
        "city": city.capitalize() if city else None,
    })