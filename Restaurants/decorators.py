from functools import wraps
from django.core.exceptions import PermissionDenied

from .Services import isOwner, isStaff

def restrict_access(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = request.user
        
        if not user.is_authenticated:
            raise PermissionDenied
        
        elif (not isStaff(user)) and (not isOwner(user)):
            raise PermissionDenied
        
        else:
            return view_func(request, *args, **kwargs)

    return _wrapped

