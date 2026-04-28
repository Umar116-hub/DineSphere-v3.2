from django.urls import path
from . import views
from .Services import get_items
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # Pages 
    path("registration/", views.registration, name="restaurant_registration"),
    path("staff-management/", views.staff_management, name="staff_management"),
    path("reservations/", views.reservations, name="reservations"),
    path("tables/", views.tables, name="tables"),
    path("holidays/", views.holidays, name="holidays"),
    path("business-info/", views.business_info, name="business_info"),
    path("reviews/", views.reviews, name="reviews"),


    # Additional Actions
    path("switch/", views.switch_business, name="switch_business"),
    path("markfinish/", views.markfinish),
    path("markcancel/", views.markcancel),
    path("hide/", views.hide),
    path("unhide/", views.unhide),


    # Business
    path('business-info/update/<int:id>/', views.updateBusiness, name='update_business'),
    path('business-info/delete/<int:id>/', views.deleteBusiness, name='delete_business'),
    
    # Tables
    path('tables/update/<int:id>/', views.updateTables, name='update_tables'),
    path('tables/delete/<int:id>/', views.deleteTables, name='delete_tables'),
    
    # Holidays
    path('holidays/update/<int:id>/', views.updateHolidays, name='update_holidays'),
    path('holidays/delete/<int:id>/', views.deleteHolidays, name='delete_holidays'),

    # Seating Types
    path('seating-type/delete/<int:id>/', views.deleteSeatingType, name='delete_seating_type'),

    # Table Sizes
    path('table-size/delete/<int:id>/', views.deleteTableSize, name='delete_table_size'),

    # getting table size and seating type
    path('get-items/', get_items, name='get_items'),

    path('download-logs/', views.download_logs, name='download_logs'),

    # Analytics view, entry point for the dashboard
    path("", views.analytics, name="analytics"),
    path("get-operational-hours/", views.get_operational_hours, name="get_operational_hours"),
    path("<str:tab>/", views.analytics),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
