from django.contrib import admin
from .models import Order,OrderProduct,Payment,Wallet,Address

# Register your models here.

admin.site.register(Order)
admin.site.register(OrderProduct)
admin.site.register(Payment)
admin.site.register(Wallet)
admin.site.register(Address)