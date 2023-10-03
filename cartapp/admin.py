from django.contrib import admin
from .models import Cart, Cartitem, Coupons, UserCoupons
# Register your models here.

admin.site.register(Cart)
admin.site.register(Cartitem)
admin.site.register(Coupons)
admin.site.register(UserCoupons)