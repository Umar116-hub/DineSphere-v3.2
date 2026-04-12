from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import User, CustomerProfile, RestaurantStaff
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect

def create_customer_user(username, email, password, dob=None, gender=None, image=None):
    if User.objects.filter(username=username).exists():
        raise ValueError("Username already taken")

    if User.objects.filter(email=email).exists():
        raise ValueError("Email already exists")

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        role='CUSTOMER'
    )

    user.date_of_birth = dob
    user.gender = gender
    user.image = image
    user.save()

    # create customer profile automatically ONLY for customers
    CustomerProfile.objects.create(user=user)

    return user


def create_owner_user(username, email, password, dob=None, gender=None, image=None):
    if User.objects.filter(username=username).exists():
        raise ValueError("Username already taken")

    if User.objects.filter(email=email).exists():
        raise ValueError("Email already exists")

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        role='OWNER'
    )

    user.date_of_birth = dob
    user.gender = gender
    user.image = image
    user.save()

    # Owners do NOT get a CustomerProfile
    return user





def add_restaurant_staff(request, username=None):
    """
    Creates a RestaurantStaff profile with the role 'STAFF'.
    Enhancement: If the user doesn't exist, auto-create a STAFF account.
    """
    if request.method == 'POST':
        if username is None:
            username = request.POST.get('username')
        
        # 1. Get the current restaurant from session
        restaurant_id = request.session.get('selected_restaurant_id')
        if not restaurant_id:
            messages.error(request, "No restaurant selected.")
            return redirect('staff_management')

        # 2. Find or create the user
        try:
            target_user = User.objects.get(username__iexact=username)
            created = False
        except User.DoesNotExist:
            # AUTO-CREATE STAFF ACCOUNT
            # For simplicity, we use the username as part of the email if not provided, 
            # but usually, we'd want an email field in the form.
            # We'll assume a generic email or just use username@dinesphere.internal
            target_user = User.objects.create_user(
                username=username,
                email=f"{username.lower()}@dinesphere.internal",
                password="DineSphere123!",
                role='STAFF'
            )
            created = True
            
        # 3. Check if they are already staff at this restaurant
        if RestaurantStaff.objects.filter(user=target_user, restaurant_id=restaurant_id).exists():
            messages.warning(request, f"{username} is already a staff member here.")
        else:
            # 4. Create the profile
            RestaurantStaff.objects.create(
                user=target_user,
                restaurant_id=restaurant_id,
                role='STAFF',
                is_premium=False
            )
            if created:
                messages.success(request, f"New account created for {username} (Role: STAFF). Default password: DineSphere123!")
            else:
                messages.success(request, f"{username} added as staff successfully!")
                
    return redirect('/business/staff-management/') 


def remove_restaurant_staff(request, staff_id):
    """Deletes a RestaurantStaff profile."""
    # We use staff_id (the ID of the RestaurantStaff record, not the User ID)
    staff_profile = get_object_or_404(RestaurantStaff, id=staff_id)
    
    # Security check: Ensure the person deleting is an OWNER of this restaurant
    owner_check = RestaurantStaff.objects.filter(
        user=request.user, 
        restaurant=staff_profile.restaurant, 
        role='OWNER'
    ).exists()

    if owner_check:
        username = staff_profile.user.username
        staff_profile.delete()
        messages.success(request, f"Access revoked for {username}.")
    else:
        messages.error(request, "You do not have permission to remove staff.")

    return redirect('/business/staff-management/') 



@require_GET
def verify_username(request):
    User = get_user_model()
    """AJAX endpoint to check if a user exists by username."""
    username = request.GET.get('username', '').strip()
    # We check if user exists (case-insensitive)
    user_exists = User.objects.filter(username__iexact=username).exists()
    
    return JsonResponse({'exists': user_exists})



def get_current_restaurant_staff(restaurant_id):
    
    return RestaurantStaff.objects.filter(
        restaurant_id=restaurant_id,
        role='STAFF'
    ).select_related('user')



