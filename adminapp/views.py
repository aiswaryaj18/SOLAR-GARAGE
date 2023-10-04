from django.shortcuts import render, redirect,  get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.cache import never_cache
from userapp.models import Product,Category,User
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from orderapp.models import Order, OrderProduct,Payment
from cartapp.models import Coupons, UserCoupons, Cartitem, Cart
from datetime import timedelta, datetime ,date
from django.utils import timezone
from django.db.models import Count, Sum
from django.db.models import Q



# Create your views here.
def admin_index(request):
    
    if request.method == "POST":
        
        return redirect("/adminapp/dashboard/")
    
    return render(request,'admin_index.html')

@login_required
def dashboard(request):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)  # Adjust the number of days as needed

    # Query the database to get daily order counts for the last five days
    daily_order_counts = (
        Order.objects
        .filter(created_at__range=(start_date, end_date))
        .values('created_at__date')
        .annotate(order_count=Count('id'))
        .order_by('created_at__date')
    )
    orders= Order.objects.all().order_by('-created_at')[:10]
    print(orders)
    # Extract dates and counts for the chart
    dates = [entry['created_at__date'].strftime('%Y-%m-%d') for entry in daily_order_counts]
    counts = [entry['order_count'] for entry in daily_order_counts]
    order=Order.objects.all()
    order_count=order.count()
    today = datetime.now()
    month=end_date-timedelta(days=30)
    total=(
    Order.objects
    .filter(created_at__range=(month, today))
    .aggregate(total_order_total=Sum('order_total')))['total_order_total']
    print(total)

    context = {
        'dates': dates,
        'counts': counts, 
        'orders': orders, 
        'order_count': order_count, 
        'total': total, 
    }

    return render(request, 'dashboard.html', context)



def sales_report(request):
    if request.method == 'POST':
        from_date_str = request.POST.get('fromDate')
        to_date_str = request.POST.get('toDate')
        from_date = datetime.strptime(from_date_str, "%Y-%m-%d").strftime("%Y-%m-%d %H:%M:%S")
        to_date = datetime.strptime(to_date_str, "%Y-%m-%d").strftime("%Y-%m-%d %H:%M:%S")
    else:
        from_date = None
        to_date = None

    orders = Order.objects.filter(created_at__range=(from_date, to_date))
    order_items = OrderProduct.objects.filter(order__in=orders)

    for order_item in order_items:
        shipping = 1500
        order_item.sub_total = order_item.product_price * order_item.quantity
        order_item.total = order_item.sub_total + shipping

    context = {
        'order_items': order_items,
    }

    return render(request, 'sales_report.html', context)



def admin_logout(request):
    return render(request,'admin_index.html')

def admin_products(request):
    products = Product.objects.select_related('category').all().order_by('id')
    context = {'products': products}
    return render(request, 'admin_products.html', context)


def add_product(request):
    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        product_images = request.FILES.get('product_images')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        price = request.POST.get('price')
        quantity = request.POST.get('quantity')
        
        category = Category.objects.get(pk=category_id)
        
        product = Product(
            product_name=product_name,
            product_images=product_images,
            category=category,
            description=description,
            price=price,
            quantity=quantity,
            is_available=True
        )
        product.save()
        
        return redirect('admin_products')
    
    categories = Category.objects.all().order_by('id')
    context = {'categories': categories}
    return render(request, 'add_product.html', context)

def edit_product(request, product_id):
    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return redirect('admin_products')
    categories = Category.objects.all().order_by('id')

    if request.method == 'POST':
        product.product_name = request.POST.get('product_name')
        product_images = request.FILES.get('product_images')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        price = request.POST.get('price')
        quantity = request.POST.get('quantity')

        category = Category.objects.get(pk=category_id)

        product.product_images = product_images
        product.category = category
        product.description = description
        product.price = price
        product.quantity = quantity
        product.save()

        return redirect('admin_products')

    context = {
        'product': product,
        'categories': categories,
    }
    return render(request, 'edit_product.html', context)

def soft_delete_product(request, product_id):
    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return redirect('admin_products')
    product.soft_deleted = True
    product.is_available = False
    product.save()
    return redirect('admin_products')


def undo_soft_delete_product(request, product_id):
    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return redirect('admin_products')
    product.soft_deleted = False
    product.is_available = True
    product.save()
    return redirect('admin_products')




def admin_category(request):
    categories = Category.objects.all().order_by('id')  
    context = {'categories': categories}
    return render(request, 'admin_category.html', context)



def add_category(request):
    if request.method == 'POST':
        category_name = request.POST.get('category_name')
        category_image = request.FILES.get('category_image')
        category_description = request.POST.get('category_description')

        category = Category(
            category_name=category_name,
            category_images=category_image,
            category_description=category_description
        )
        category.save()

        return redirect('admin_category')

    return render(request, 'add_category.html')


def edit_category(request, category_id):
    try:
        category = Category.objects.get(pk=category_id)
    except Category.DoesNotExist:
        return redirect('admin_category')

    if request.method == 'POST':
        category_name = request.POST.get('category_name')
        category_image = request.FILES.get('category_image')
        category_description = request.POST.get('category_description')

        category.category_name = category_name
        category.category_description = category_description
        if category_image:
            category.category_images = category_image
        category.save()

        return redirect('admin_category')

    context = {'category': category}
    return render(request, 'edit_category.html', context)





def delete_category(request, category_id):
    try:
        category = Category.objects.get(pk=category_id)
        category.delete()
    except Category.DoesNotExist:
        pass
    return redirect('admin_category')


def admin_users(request):
    
    users = User.objects.all().order_by('id')
        
    context = {
        'users': users,
    }
    
    return render(request,'admin_users.html',context)


def admin_orders(request):
    orders = Order.objects.filter(is_ordered=True).order_by('-created_at')
    context = {'orders': orders}
    return render(request, 'admin_orders.html', context)



@login_required
def update_order_status(request, order_id, new_status):
    
    order = get_object_or_404(Order, pk=order_id)
    
    if new_status == 'New':
        order.status = 'New'
    elif new_status == 'Accepted':
        order.status = 'Accepted'
    elif new_status == 'Completed':
        order.status = 'Completed'
    elif new_status == 'Cancelled':
        order.status = 'Cancelled'
    
    order.save()
    
    messages.success(request, f"Order #{order.order_number} has been updated to '{new_status}' status.")
    
    return redirect('admin_orders')



@login_required
def admin_order_details(request, order_id):
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

    return render(request, 'admin_order_details.html', context)



def admin_coupons(request):
    if request.user.is_superadmin:
        coupons = Coupons.objects.all()
        context = {'coupons': coupons}
        return render(request, 'admin_coupons.html', context)
    else:
        return HttpResponseForbidden("You don't have permission to access this page.")
    
    


@login_required
def admin_add_coupons(request):
    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code')
        description = request.POST.get('description')
        minimum_amount = request.POST.get('minimum_amount')
        discount = request.POST.get('discount')
        valid_from = request.POST.get('valid_from')
        valid_to = request.POST.get('valid_to')

        try:
            minimum_amount = int(minimum_amount)
            discount = int(discount)
        except ValueError:
            messages.error(request, "Minimum Amount and Discount must be integers.")
            return redirect('admin_add_coupons')

        coupon = Coupons(
            coupon_code=coupon_code,
            description=description,
            minimum_amount=minimum_amount,
            discount=discount,
            valid_from=valid_from,
            valid_to=valid_to
        )
        coupon.save()
        messages.success(request, "Coupon added successfully.")
        return redirect('admin_coupons')

    return render(request, 'admin_add_coupons.html')




@login_required
def admin_edit_coupons(request, coupon_id):
    try:
        coupon = Coupons.objects.get(pk=coupon_id)
    except Coupons.DoesNotExist:
        return redirect('admin_coupons')

    if request.method == 'POST':
        coupon.coupon_code = request.POST.get('coupon_code')
        coupon.description = request.POST.get('description')
        coupon.minimum_amount = int(request.POST.get('minimum_amount'))
        coupon.discount = int(request.POST.get('discount'))
        coupon.valid_from = request.POST.get('valid_from')
        coupon.valid_to = request.POST.get('valid_to')
        
        coupon.save()
        
        return redirect('admin_coupons')

    context = {'coupon': coupon}
    return render(request, 'admin_edit_coupons.html', context)




@login_required
def admin_delete_coupons(request, coupon_id):
    try:
        coupon = Coupons.objects.get(pk=coupon_id)
    except Coupons.DoesNotExist:
        return redirect('admin_coupons')

    if request.method == 'POST':
        coupon.delete()
        messages.success(request, "Coupon deleted successfully.")
    
    return redirect('admin_coupons')

def admin_banners(request):
    return render(request,'admin_banners.html')

def user_block(request,user_id):
    if request.method == 'POST':
         user = User.objects.get(pk=user_id)
         user.is_active =False
         user.save()
    return redirect('admin_users')

def user_unblock(request,user_id):
    if request.method == 'POST':
        user = User.objects.get(pk=user_id)
        user.is_active=True
        user.save()
    return redirect('admin_users')


def admin_search(request):
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products = Product.objects.order_by('-description').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
    
    context ={
        'products': products,
    }
    return render(request,'dashboard.html', context )