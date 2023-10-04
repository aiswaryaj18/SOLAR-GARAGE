from django.shortcuts import render,redirect,get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from userapp.models import Product
from cartapp.models import Cart, Cartitem, Coupons
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from orderapp.models import Address
from django.contrib import messages

# Create your views here.

def _cart_id(request):
    cart =request.session.session_key
    if not cart:
        cart= request.session.create()
    return cart


def calculate_cartitem_count(user):
    try:
        # Get the user's cart
        cart = Cart.objects.get(user=user)

        # Count the number of active cart items for the user
        cartitem_count = Cartitem.objects.filter(cart=cart, is_active=True).count()
    except Cart.DoesNotExist:
        # Handle the case where the user doesn't have a cart
        cartitem_count = 0

    return redirect( 'navbar')




def add_cart(request, product_id):
    current_user = request.user
    product = Product.objects.get(id=product_id)

    if current_user.is_authenticated:
        cart_item = Cartitem.objects.filter(product=product, user=current_user).first()
        if cart_item:
            if cart_item.quantity < product.quantity:
                cart_item.quantity += 1
                cart_item.save()
                return redirect('cart')
                
            else:
                messages.warning(request, 'Product quantity in cart exceeds available quantity.')
        else:
            cart_item = Cartitem.objects.create(
                product=product,
                quantity=1,
                user=current_user,
            )
            
        messages.success(request, 'Product Added to Cart')
            
        return redirect('products')
    
    else:
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(
                cart_id=_cart_id(request)
            )
        cart.save()

        cart_item = Cartitem.objects.filter(product=product, cart=cart).first()
        if cart_item:
            if cart_item.quantity < product.quantity:
                cart_item.quantity += 1
                cart_item.save()
                return redirect('cart')
            else:
                messages.warning(request, 'Product quantity in cart exceeds available quantity.')
        else:
            cart_item = Cartitem.objects.create(
                product=product,
                quantity=1,
                cart=cart,
            )
        messages.success(request, 'Product Added to Cart')
        return redirect('products')
    

def remove_cart(request, product_id):
    product = Product.objects.filter(id=product_id).first()
    
    try:
        if request.user.is_authenticated:
            cart_item = Cartitem.objects.filter(product=product, user=request.user).first()
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = Cartitem.objects.filter(product=product, cart=cart).first()
        
        if cart_item:
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()
    except ObjectDoesNotExist:
        pass

    return redirect('cart')

def remove_cart_item(request, product_id):
    
    product = Product.objects.filter(id=product_id).first()
    if request.user.is_authenticated:
        cart_item = Cartitem.objects.get(product=product, user=request.user)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = Cartitem.objects.get(product=product, cart=cart)
    cart_item.delete()
    return redirect('cart')


def cart(request, total=0, sub_total=0, quantity=0, cart_items=None):
    try:
        shipping = 0
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = Cartitem.objects.filter(user=request.user, is_active =True)
        else:
            cart= Cart.objects.get(cart_id= _cart_id(request))
            cart_items= Cartitem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            cart_item.sub_total = cart_item.product.price * cart_item.quantity
            cart_item.save()  
            sub_total += cart_item.sub_total
            total += (cart_item.product.price * cart_item.quantity)
            quantity +=  cart_item.quantity
            # sub_total = (cart_item.product.price * cart_item.quantity)
        shipping = 1500
        grand_total = total + shipping
        
    except ObjectDoesNotExist:
        pass
    
    context ={
        'total' :total,
        'quantity' : quantity,
        'cart_items' : cart_items,
        'shipping' : shipping,
        'grand_total' :grand_total,
    }
            
    return render(request,'cart.html', context)

