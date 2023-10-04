from django.shortcuts import render, redirect
from cartapp.models import Cartitem, Cart, Coupons, UserCoupons
from orderapp.models import Order, Payment, OrderProduct, Address
from orderapp.forms import OrderForm
import datetime
from userapp.models import User
from django.db import transaction
from django.conf import settings
from django.utils import timezone  
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from cartapp.views import _cart_id

# Create your views here.



@transaction.atomic
def cash_on_delivery(request, order_number):
    current_user = request.user
    try:
        order = Order.objects.get(order_number=order_number, user=current_user, is_ordered=False)
    except Order.DoesNotExist:
        return redirect('order_confirmed')
    
    total_amount = order.order_total 
   
    payment = Payment(user=current_user, payment_method="Cash On Delivery", amount_paid=total_amount, status="Not Paid")
    payment.save()
    
   
    order.is_ordered = True
    order.payment = payment
    order.save()
    
    
    cart_items = Cartitem.objects.filter(user=current_user)
    
    
    for cart_item in cart_items:
        product=cart_item.product
        stock=product.quantity-cart_item.quantity
        product.quantity=stock
        product.save()
        order_product = OrderProduct(
            order=order,
            payment=payment,
            user=current_user,
            product=cart_item.product,
            quantity=cart_item.quantity,
            product_price=cart_item.product.price,
            ordered=True,
        )
        order_product.save()
    
    cart_items.delete()
    
    context = {'order': order}

    return render(request, 'order_confirmed.html', context)


def payments(request, order_id):
    current_user = request.user
    coupon_code =   request.session['coupon_code']
    coupon = Coupons.objects.get(coupon_code=coupon_code)
    cart_items = Cartitem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('products')
    
    shipping = 0
    grand_total = 0
    total = 0
    quantity = 0

    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity

    shipping = 1500
    grand_total = total + shipping - coupon.discount
    
    try:
        order = Order.objects.get(user=current_user, is_ordered=False, id=order_id)
    except Order.DoesNotExist:
        return redirect('payments')
        
        
    context = {
        'order': order,
        'cart_items': cart_items,
        'total': total,
        'shipping': shipping,
        'discount': coupon.discount,
        'grand_total': grand_total,
    }
    return render(request, 'payments.html', context)


def set_default_address(request, address_id):
    addr_list = Address.objects.filter(user=request.user)
    for a in addr_list:
        a.is_default = False
        a.save()
    address = Address.objects.get(id=address_id)
    address.is_default=True
    address.save()
    return redirect('checkout')


def checkout(request, total=0 , sub_total=0, quantity=0, cart_items=None):
    try:
        shipping = 0
        grand_total = 0
        coupon_discount = 0

        if request.user.is_authenticated:
            cart_items = Cartitem.objects.filter(user=request.user, is_active=True)
            
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = Cartitem.objects.filter(cart=cart, is_active=True)


        for cart_item in cart_items:
            cart_item.sub_total = cart_item.product.price * cart_item.quantity
            cart_item.save()  
            sub_total += cart_item.sub_total
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        
        shipping = 1500
        grand_total = total+ shipping


    except Cart.DoesNotExist:
        pass
    except Cartitem.DoesNotExist:
        pass

    address_list = Address.objects.filter(user=request.user)
    default_address = address_list.filter(is_default=True).first()
    coupons = Coupons.objects.all()
    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'shipping':shipping,
        'grand_total': grand_total,
        'address_list': address_list,
        'default_address': default_address,
        'coupons': coupons,
        'coupon_discount':coupon_discount
    }
    return render(request, 'checkout.html', context)


@login_required
def place_order(request, total=0, quantity=0):
    current_user = request.user
    coupons = Coupons.objects.all()


    cart_items = Cartitem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('products')
    
    shipping = 0
    grand_total = 0
    discount = 0
    
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity

    shipping = 1500
    grand_total = total + shipping
    
    if request.method == 'POST':
        
        try:
            address = Address.objects.get(user=request.user,is_default=True)
        except:
            messages.warning(request, 'No delivery address exixts! Add a address and try again')
            return redirect('checkout')
        
        
        data = Order()
        data.user = current_user
        data.first_name = address.first_name
        data.last_name = address.last_name
        data.phone = address.phone
        data.email = address.email
        data.address_line_1 = address.address_line_1
        data.address_line_2 = address.address_line_2
        data.city = address.city
        data.pincode = address.pincode
        data.order_total = grand_total
        data.shipping = shipping
        data.ip = request.META.get('REMOTE_ADDR')
        data.save()

        yr = int(datetime.date.today().strftime('%Y'))
        dt = int(datetime.date.today().strftime('%d'))
        mt = int(datetime.date.today().strftime('%m'))
        d = datetime.date(yr,mt,dt)
        current_date = d.strftime("%Y%m%d")
        order_number = current_date + str(data.id)
        data.order_number = order_number
        data.save()

    
        order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
        context = {
            'order': order,
            'cart_items': cart_items,
            'total': total,
            'shipping': shipping,
            'discount': discount,
            'grand_total': grand_total,
            'coupons': coupons,
            
        }
        return render(request, 'payments.html', context)
    else:
        return redirect('checkout')
    

def apply_coupon(request):

    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code')
        order_id = request.POST.get('order_id')
        request.session['coupon_code'] = coupon_code


        try:
            coupon = Coupons.objects.get(coupon_code=coupon_code)
            order = Order.objects.get(id=order_id)
            if coupon.valid_from <= timezone.now() <= coupon.valid_to:

                if order.order_total >= coupon.minimum_amount:
                    if coupon.is_used_by_user(request.user):
                        messages.error(request, 'Coupon has already been Used')
                    else:
                        updated_total = order.order_total - float(coupon.discount)
                        order.order_total = updated_total
                        order.save()

                        used_coupons = UserCoupons(user = request.user, coupon = coupon, is_used = True)
                        used_coupons.save()

                        return redirect('payments', order_id)
                
                else:
                    messages.error(request, 'Coupon is not Applicable for Order Total')
            else:
                messages.error(request, 'Coupon is not Applicable for the current date')

        except Coupons.DoesNotExist:
            messages.error(request, 'Coupon code is Invalid')

    return redirect('payments', order_id)
    
# def razor(request):
#     current_user = request.user
#     cart_items = Cartitem.objects.filter(user=current_user)


#     total = 0
#     quantity = 0

#     for cart_item in cart_items:
#         total += (cart_item.product.price * cart_item.quantity)
#         quantity += cart_item.quantity

#     shipping = 1500
#     grand_total = total  + shipping

#     if request.method == "POST":
#         form = OrderForm(request.POST)
#         if form.is_valid():
#             data = Order()
#             data.user = current_user
#             data.first_name = form.cleaned_data['first_name']
#             data.last_name = form.cleaned_data['last_name']
#             data.email = form.cleaned_data['email']
#             data.phone = form.cleaned_data['phone']
#             data.address_line_1 = form.cleaned_data['address_line_1']
#             data.address_line_2 = form.cleaned_data['address_line_2']
#             data.city = form.cleaned_data['city']
#             data.pincode = form.cleaned_data['pincode']
#             data.order_note = form.cleaned_data['order_note']
#             data.order_total = grand_total
#             data.shipping = shipping
#             data.ip = request.META.get('REMOTE_ADDR')
#             data.save()

#             yr = int(datetime.date.today().strftime('%Y'))
#             dt = int(datetime.date.today().strftime('%d'))
#             mt = int(datetime.date.today().strftime('%m'))
#             d = datetime.date(yr, mt, dt)
#             current_date = d.strftime("%Y%m%d")
#             order_number = current_date + str(data.id)
#             data.order_number = order_number
#             data.save()

#             payment_amount_paise = int(grand_total * 100)

#             client = razorpay.Client(auth=(settings.KEY, settings.SECRET))
#             payment = client.order.create({
#                 'amount': payment_amount_paise,
#                 'currency': 'INR',
#                 'payment_capture': 1,
#                 'external_order_id': order_number,
#             })

#             return redirect(payment['short_url'])

#     return redirect('checkout')



def order_confirmed(request, order_number):
    user = request.user
    order = Order.objects.get(order_number=order_number)

    context = {
        'order': order,
    }
    
    return render(request, 'order_confirmed.html',context)

def order_invoice(request, order_id):
    user = request.user
    try:
        order = Order.objects.get(id=order_id)
        order_items = OrderProduct.objects.filter(order=order)
        coupon_code = request.session.get('coupon_code', None) 
        coupon = None 

        if coupon_code:
            try:
                coupon = Coupons.objects.get(coupon_code=coupon_code)
            except Coupons.DoesNotExist:
                coupon = None

        payment = Payment.objects.get(order=order)
        cart_items = Cartitem.objects.filter(user=user)

        total = 0
        shipping = 0
        grand_total = 0  

        subtotal = 0  
        for order_item in order_items:
            order_item_total = order_item.product.price * order_item.quantity
            total = order_item_total  
            subtotal += order_item_total

        shipping = 1500  

        grand_total = subtotal + shipping - (coupon.discount if coupon else 0)  

        context = {
            'order': order,
            'order_items': order_items,
            'payment': payment,
            'grand_total': grand_total,
            'cart_items': cart_items,
            'total': total,
            'discount': coupon.discount if coupon else 0,  
            'subtotal': subtotal,
        }

    except Order.DoesNotExist:
        messages.error(request, 'Order does not exist.')  
        return redirect('products')  
    return render(request, 'order_invoice.html', context)



@transaction.atomic
def confirm_razorpay_payment(request, order_number):
    current_user = request.user
    try:
        order = Order.objects.get(order_number=order_number, user=current_user, is_ordered=False)
    except Order.DoesNotExist:
        return redirect('order_confirmed')
    
    total_amount = order.order_total 

    payment = Payment(
        user=current_user,
        payment_method="Razorpay",
        status="Paid",
        amount_paid=total_amount,
    )
    payment.save()

    order.is_ordered = True
    order.order_number = order_number
    order.payment = payment
    order.save()

    cart_items = Cartitem.objects.filter(user=current_user)
    for cart_item in cart_items:
        product=cart_item.product
        stock=product.quantity-cart_item.quantity
        product.quantity=stock
        product.save()
        order_product = OrderProduct(
            order=order,
            payment=payment,
            user=current_user,
            product=cart_item.product,
            quantity=cart_item.quantity,
            product_price=cart_item.product.price,
            ordered=True,
        )
        order_product.save()

    cart_items.delete()

    context = {'order': order}
    return render(request, 'order_confirmed.html', context)