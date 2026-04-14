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





def add_restaurant_staff(request):
    """
    Creates a new STAFF user and a corresponding RestaurantStaff profile.
    """
    if request.method == 'POST':
        # 1. Extract details from POST
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        phone = request.POST.get('phone', '').strip()
        gender = request.POST.get('gender', 'O')
        
        # 2. Get the current restaurant from session
        restaurant_id = request.session.get('selected_restaurant_id')
        if not restaurant_id:
            messages.error(request, "No restaurant selected.")
            return redirect('staff_management')

        # 3. Validations
        if not email or not password or not first_name:
            messages.error(request, "First Name, Email, and Password are required.")
            return redirect('staff_management')

        if User.objects.filter(email=email).exists():
            messages.error(request, "A user with this email already exists.")
            return redirect('staff_management')

        # Generate a username from email if not provided (using prefix)
        username = email.split('@')[0]
        # Ensure username uniqueness
        original_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{original_username}{counter}"
            counter += 1

        # 4. Create the user
        try:
            target_user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role='STAFF'
            )
            target_user.phone = phone
            target_user.gender = gender
            target_user.save()

            # 5. Create the RestaurantStaff profile
            RestaurantStaff.objects.create(
                user=target_user,
                restaurant_id=restaurant_id,
                role='STAFF',
                is_premium=False
            )
            messages.success(request, f"Staff member {first_name} {last_name} added successfully!")

        except Exception as e:
            messages.error(request, f"Error creating staff: {str(e)}")
            
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



