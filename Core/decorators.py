from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from urllib.parse import quote

def customer_required(view_func):
    """
    Decorator for views that checks that the logged in user is a customer,
    redirects to the log-in page if necessary or raises PermissionDenied.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # 🟢 Allow guests to BROWSE (GET) but protect transactions
        if not request.user.is_authenticated:
            if request.method == 'GET':
                return view_func(request, *args, **kwargs)
            return redirect(f"{reverse('auth')}?next={quote(request.path)}")
        
        # 🔴 Prevent Owners/Staff from making bookings (POST), but allow them to preview (GET)
        if request.user.role == 'CUSTOMER' or request.method == 'GET':
            return view_func(request, *args, **kwargs)
        
        messages.error(request, "Business accounts (Owners/Staff) cannot access booking features. Please use a regular customer account to make a reservation.")
        return redirect('home')
        
    return _wrapped_view
