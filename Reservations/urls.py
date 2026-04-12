from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('checkout/', views.checkout_view, name='checkout'),
    path('placeOrder/', views.placeOrder_view, name='place-order'),
    path('order-success/<int:booking_id>/', views.order_success, name='order_success'),
    path('invoice/<int:booking_id>/', views.view_invoice, name='view_invoice'),
    path('get-unavailable-tables/', views.get_unavailable_tables, name='get_unavailable_tables'),
    path('<slug:Restaurant_name>/', views.booking_view, name='booking'),
    path('<slug:Restaurant_name>/postReview/', views.post_review, name='post-review'),
]  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    




