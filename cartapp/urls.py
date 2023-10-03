from django.urls import path
from cartapp import views


urlpatterns = [
    path('', views.cart, name='cart'),
    path('calculate_cartitem_count/', views.calculate_cartitem_count, name='calculate_cartitem_count'),
    path('add_cart/<int:product_id>/', views.add_cart, name='add_cart'),
    path('remove_cart/<int:product_id>/', views.remove_cart, name='remove_cart'),
    path('remove_cart_item/<int:product_id>/', views.remove_cart_item, name='remove_cart_item'),
]