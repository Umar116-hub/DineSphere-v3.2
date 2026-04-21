from functools import wraps
from django.core.exceptions import PermissionDenied

from django.shortcuts import redirect
from django.contrib import messages
from .Services import isOwner, isStaff

def restrict_access(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = request.user
        
        if not user.is_authenticated:
            raise PermissionDenied
        
        # Check if the user is STAFF and trying to access restricted views
        if isStaff(user):
            restricted_views = [
                'analytics',
                'staff_management',
                'holidays',
                'business_info',
                'restaurant_registration'
            ]
            
            # Use request.resolver_match.view_name to identify the target view
            from django.urls import resolve
            current_url_name = resolve(request.path_info).url_name
            
            if current_url_name in restricted_views:
                messages.error(request, "Access Denied: Staff members cannot access this section.")
                return redirect('reservations') # Redirect to an allowed page
        
        elif not isOwner(user):
            raise PermissionDenied
        
        return view_func(request, *args, **kwargs)

    return _wrapped

