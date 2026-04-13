from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .services import (
    verify_username,
    add_restaurant_staff,
    remove_restaurant_staff
)

urlpatterns = [
    path('auth/', views.auth, name='auth'),
    path('business-register/', views.business_register, name='business_register'),
    path('login/', views.login_user, name='login'),
    path('signup/', views.signup_user, name='signup'),
    path('logout/', views.logout_user, name='logout'),

    # Staff Management
    path('verify-username/', verify_username, name='verify_username'),
    path('remove-staff/<int:staff_id>/', remove_restaurant_staff, name='remove_staff'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    

