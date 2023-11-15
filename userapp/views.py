from django.shortcuts import render, redirect,  get_object_or_404
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import Product,Category, User, Wishlist
from django.contrib.auth.decorators import login_required
from cartapp.models import Cart, Cartitem, UserCoupons, Coupons
from django.views.decorators.cache import never_cache
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import HttpResponse
from django.db.models import Q
from cartapp.views import _cart_id
from orderapp.forms import OrderForm
from orderapp.models import Order, OrderProduct, Payment, Wallet, Address
import requests
from django.contrib import auth
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.validators import validate_email



# Create your views here.
@never_cache
def index(request):
    
    categories = Category.objects.all()

    context = {
        'categories': categories,
    }
    
    return render(request,'index.html', context)



def about(request):
    return render(request,'about.html')


def products(request):
    
    categories = Category.objects.all()
    selected_category_id = request.GET.get('category')

    if selected_category_id:
        selected_category = Category.objects.get(id=selected_category_id)
        products = Product.objects.filter(category=selected_category, is_available=True)
        paginator = Paginator(products, 3)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
    else:
        products = Product.objects.filter(is_available=True).order_by('id')
        paginator = Paginator(products, 2)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)

    context = {
        'categories': categories,
        'products': paged_products,
    }
    
    return render(request,'products.html', context)

def product_details(request, category_id, product_id):
    
    categories = Category.objects.all()

    try:
        selected_category = Category.objects.get(id=category_id)
        single_product = Product.objects.get(category=selected_category, id=product_id, is_available=True)
    except Exception as e:
        raise e
    
    context = {
        'single_product': single_product,
        'is_out_of_stock': single_product.quantity <= 0,
        'product': single_product,
    }
    
    return render(request,'product_details.html', context)


def contact(request):
    return render(request,'contact.html')



def user_profile(request):
    return render(request,'user_profile.html')


def userlogin(request):
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user is not None:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists = Cartitem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_item = Cartitem.objects.filter(cart=cart)

                    for item in cart_item:
                        item.user = user
                        item.save()
            except:
                pass
            login(request, user)
            url = request.META.get('HTTP_REFERER')
            try:
                query = requests.utils.urlparse(url).query
                params = dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    nextPage = params['next']
                    return redirect(nextPage)
            except:
                return redirect('/')
            
        else:
            messages.error(request, "Email or password is incorrect")

    return render(request, 'userlogin.html')



def forgot_password(request):

    if request.method == "POST":
        email = request.POST['email']
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email__exact=email)

            current_site = get_current_site(request)
            mail_subject = "Reset Your Password"
            message = render_to_string('password_verification.html',{
                'user': user,
                'domain': current_site,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email  = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            messages.success(request,"Password reset email has been sent to your email address ")
            return redirect('userlogin')

        else:
            messages.warning(request, 'Account does not exist!')
    else:
        return render(request, 'forgot_password.html')




def password_validation(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'Please Reset your Password!!')
        return redirect('reset_password')
    else:
        messages.warning(request, 'Link has been expired')
        return redirect('userlogin')


def reset_password(request):

    if request.method == "POST":
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password == confirm_password:
            uid = request.session.get('uid')
            user = User.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'Password reset Successfull')
            return redirect('userlogin')

        else:
            messages.warning(request, 'Passwords do not match')
            return redirect("reset_password")
    else:
        return render(request, 'reset_password.html')



def usersignup(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        mobile = request.POST.get("mobile")
        password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        try:
            validate_email(email)
        except ValidationError:
            messages.warning(request, "Invalid email address")
            return redirect('usersignup')

        if password != confirm_password:
            messages.warning(request, "Passwords do not match")
            return redirect('usersignup')

        if User.objects.filter(name=name).exists():
            messages.warning(request, "Username is already taken")
            return redirect('usersignup')

        if User.objects.filter(email=email).exists():
            messages.warning(request, "Email is already taken")
            return redirect('usersignup')

        if User.objects.filter(mobile=mobile).exists():
            messages.warning(request, "Mobile Number is already taken")
            return redirect('usersignup')

        user = User(name=name, email=email, mobile=mobile)
        user.set_password(password)
        user.save()

        current_site = get_current_site(request)
        mail_subject = "Please acivate your Account"
        message = render_to_string('signup_verification.html',{
            'user': user,
            'domain': current_site,
            'uid':urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
        })
        to_email = email
        send_email  = EmailMessage(mail_subject, message, to=[to_email])
        send_email.send()
        messages.success(request, 'Please click on the link send to your email to Activate your Account')

    return render(request, 'usersignup.html')



def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.is_staff = True
        user.save()
        messages.success(request, 'Congrats, Your Account is Activated. Please Login!!')
        return redirect('userlogin')
    else:
        messages.warning(request, 'Invalid Activation Link.')
        return redirect('usersignup')




# def usersignupotp(request,id):
#     if request.method=='POST':
#         otp=request.POST.get('otp')
#         user=User.objects.get(id=id)

#         print(user.id)
        # if otp==user.otp:
        #     login(request,user)
        # user_details=User.objects.all()
        # context={
        #     'user':user_details
        # }
        # return render(request,'user/index.html',context)
    #     return redirect('index')
    # context={
    #     'id':id
    # }
    # return render(request,'usersignupotp.html',context) 

def usersignupotp(request):
    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        stored_data = request.session.get("signup_user_data")
        print("Entered OTP:", entered_otp)
        print("Stored OTP:", stored_data["otp"])

        if stored_data and entered_otp == stored_data["otp"]:
            
            user = User(name=stored_data["name"], email=stored_data["email"], mobile=stored_data["mobile"])
            user.set_password(stored_data["password"])
            user.is_active =True
            user.is_staff =True
            user.save()
            
            # Clear stored user data from session
            del request.session["signup_user_data"]
            
            return redirect("userlogin")
        else:
            # Incorrect OTP
            # Handle this error and redirect back to OTP verification page
            pass

    return render(request, "usersignupotp.html")

@login_required
def userlogout(request):
    logout(request)
    return redirect('/')

def search(request):
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products = Product.objects.order_by('-description').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
    
    context ={
        'products': products,
    }
    return render(request,'products.html', context )

@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
    order_products = OrderProduct.objects.filter(user=request.user)
    context = {
        'orders': orders,
        'order_products': order_products,
    }
    return render(request, 'my_orders.html', context)

@login_required
def order_details(request, order_id):
    order_products = OrderProduct.objects.filter(order__user=request.user, order__id=order_id)
    orders = Order.objects.filter(is_ordered=True, id=order_id)
    
    payments = Payment.objects.filter(order__id=order_id)

    for order_product in order_products:
        order_product.total = order_product.quantity * order_product.product_price

    context = {
        'order_products': order_products,
        'orders': orders,
        'payments': payments,
    }

    return render(request, 'order_details.html', context)


@login_required
def cancel_order(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)

        if order.status in ["New", "Accepted"]:
            order.status = "Cancelled"
            order.save()
            messages.success(request, 'Order cancelled.')
        else:
            messages.warning(request, 'Order cannot be cancelled.')

    except Order.DoesNotExist:
        messages.warning(request, 'Order not found.')

    return redirect('my_orders')

@login_required(login_url='login')
def return_order(request, order_id):
    order = Order.objects.get(id=order_id, user=request.user)

    if order.status == 'Completed':
        user = request.user
        wallet, created = Wallet.objects.get_or_create(user=user)

        wallet.amount += order.order_total
        wallet.amount = round(wallet.amount, 2)
        wallet.save()

        order.status = 'Returned'
        order.save()

    return redirect('my_orders')


@login_required(login_url='userlogin')
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    user = request.user

    if not Wishlist.objects.filter(user=user, product=product).exists():
        Wishlist.objects.create(user=user, product=product)
        messages.success(request, 'Product added to wishlist.')
    else:
        messages.warning(request, 'Product is already in the wishlist.')

    return redirect('product_details', category_id=product.category.id, product_id=product.id)



@login_required(login_url='userlogin')
def view_wishlist(request):
    user = request.user

    wishlist_items = Wishlist.objects.filter(user=user)
    wishlist_products = [item.product for item in wishlist_items]

    return render(request, 'wishlist.html', {'wishlist_products': wishlist_products})


@login_required
def remove_from_wishlist(request, product_id):
    user = request.user
    product = get_object_or_404(Product, id=product_id)
    
    try:
        wishlist_item = Wishlist.objects.get(user=user, product=product)
        wishlist_item.delete()
        messages.success(request, 'Product removed from wishlist.')
    except Wishlist.DoesNotExist:
        messages.warning(request, 'Product was not in your wishlist.')

    return redirect('view_wishlist')




# @login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']
        
        user = User.objects.get(name__exact=request.user.name)
    
        if new_password == confirm_password:
            success = user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()
                auth.logout(request)
                messages.success(request, 'Password Changed Successfully')
                return redirect('change_password')
            else:
                messages.error(request, 'Please enter valid current password')
                return redirect('change_password')
        else:
            messages.error(request, 'Password does not match')
            return redirect('change_password')

    return render(request, 'change_password.html')


# @login_required
# def coupons(request):
#     user_coupons = UserCoupons.objects.filter(user=request.user)
#     coupon_status = {}
#     for user_coupon in user_coupons:
#         coupon_status[user_coupon.coupon] = 'Used' if user_coupon.is_used else 'Active'

#     context = {
#         'coupon_status': coupon_status,
#     }

#     return render(request, 'coupons.html', context)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        user = request.user
        new_name = request.POST.get('name')
        new_mobile = request.POST.get('mobile')
        new_email = request.POST.get('email')

        if User.objects.filter(name=new_name).exclude(id=user.id).exists():
            messages.error(request, 'Username is already taken')
            return redirect('user_profile')

        if User.objects.filter(email=new_email).exclude(id=user.id).exists():
            messages.error(request, 'Email is already taken')
            return redirect('user_profile')

        if User.objects.filter(mobile=new_mobile).exclude(id=user.id).exists():
            messages.error(request, 'Mobile number is already taken')
            return redirect('user_profile')

        user.name = new_name
        user.mobile = new_mobile
        user.email = new_email
        user.save()

        messages.success(request, 'Profile updated successfully')
        return redirect('user_profile')

    return render(request, 'user_profile.html')




@login_required
def add_address(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        address_line_1 = request.POST.get('address_line_1')
        address_line_2 = request.POST.get('address_line_2')
        city = request.POST.get('city')
        pincode = request.POST.get('pincode')


        address = Address(user=request.user, first_name=first_name, last_name=last_name, phone=phone, email=email, address_line_1=address_line_1, address_line_2=address_line_2, city=city, pincode=pincode)
        address.save()


        if request.user.is_authenticated:
            Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
            address.is_default = True
            address.save()

        source = request.GET.get('source', 'checkout')
        messages.success(request, 'New address added successfully.')
        
        if source == 'checkout':
            return redirect('checkout')
        else:
            return redirect('add_address')
    else:
        return render(request, 'add_address.html')


@login_required
def manage_address(request):
    current_user = request.user
    addresses = Address.objects.filter(user=current_user)
    context = {
        'addresses': addresses,
    }
    return render(request, 'manage_address.html', context)


@login_required
def edit_address(request, address_id):
    address = Address.objects.get(pk=address_id)

    if request.method == 'POST':

        address.first_name = request.POST.get('first_name')
        address.last_name = request.POST.get('last_name')
        address.email = request.POST.get('email')
        address.phone = request.POST.get('phone')
        address.address_line_1 = request.POST.get('address_line_1')
        address.address_line_2 = request.POST.get('address_line_2')
        address.city = request.POST.get('city')
        address.pincode = request.POST.get('pincode')

        address.save()

        messages.success(request, 'Address updated successfully.')

        return redirect('edit_address', address_id=address.id)

    

    context = {
        'address': address,
    }
    return render(request, 'edit_address.html', context)



def delete_address(request, address_id):

    address = Address.objects.get(pk=address_id)
    address.delete()

    return redirect('manage_address')



def coupons(request):
    if request.user.is_authenticated:
        coupons = Coupons.objects.all()
        context = {'coupons': coupons}
        return render(request, 'coupons.html', context)
    else:
        return HttpResponseForbidden("You don't have permission to access this page.")


@login_required(login_url='user_login')
def my_wallet(request):
    current_user = request.user
    try:
        wallet = Wallet.objects.get(user=current_user)
    except Wallet.DoesNotExist:
        wallet = Wallet.objects.create(user=current_user, amount=0)
    wallet_amount = wallet.amount
  
    context = {'wallet_amount': wallet_amount}

    return render(request, 'wallet.html', context)


@login_required(login_url='login')
def wallet_pay(request, order_id):
    user = request.user
    order = Order.objects.get(id = order_id)
    try:
        wallet = Wallet.objects.get(user = user)
        
    except:
        wallet = Wallet.objects.create(user = user, amount=0)
        wallet.save()
        
    if wallet.amount>order.order_total:
        payment = Payment.objects.create(user=user, payment_method='Wallet', amount_paid = order.order_total, status='Paid')
        payment.save()
        order.is_ordered = True
        
        order.payment = payment
        order.save()
        wallet.amount -= order.order_total
        wallet.save()

        cart_items = Cartitem.objects.filter(user=user)
    
        for cart_item in cart_items:
            order_product = OrderProduct(
                order=order,
                payment=payment,
                user=user,
                product=cart_item.product,
                quantity=cart_item.quantity,
                product_price=cart_item.product.price,
                ordered=True,
            )
            order_product.save()
        
        cart_items.delete()
        
    else:
        messages.warning(request, 'Not Enough Balance in Wallet')
        return redirect('payments', order_id)
    context = {
        'order': order,
        'order_number': order.order_number,
        }
    return render(request, 'order_confirmed.html', context)