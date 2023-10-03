from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

# Create your models here.

class User_manager(BaseUserManager):
    def create_user(self, name, email, password=None):
        if not email:
            raise ValueError('User must have an email address')
        
        user = self.model(
            email = self.normalize_email(email), 
            name = name
        )


        user.set_password(password)
        user.save(using=self._db)
        return user
    

    def create_superuser(self, name, email, password):
        user = self.create_user(
            email = self.normalize_email(email),
            password = password,
            name = name,
        )

        user.is_admin = True
        user.is_active = True
        user.is_staff = True
        user.is_superadmin = True
        user.save(using=self._db)
        return user
    


class User(AbstractBaseUser):
    name = models.CharField(max_length=50)
    email = models.EmailField(max_length=100, unique=True)
    mobile = models.CharField(max_length=50, unique=True, blank=False)

    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_superadmin = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    objects = User_manager()

    def __str__(self):
        return self.email
    
    def has_perm(self, perm, obj=None):
        return self.is_admin
    
    def has_module_perms(self, add_label):
        return True
    




class Category(models.Model):
    category_name = models.CharField(max_length=50, unique=True)
    category_images = models.ImageField(upload_to='photos/categories', blank=True)
    category_description = models.TextField(max_length=500, blank=True)

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'


    def __str__(self):
        return self.category_name
    



class Product(models.Model):
    product_name = models.CharField(max_length=200, unique=True)
    product_images = models.ImageField(upload_to='photos/products')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.TextField(max_length=500, blank=True)
    price = models.IntegerField()
    quantity = models.IntegerField()
    is_available = models.BooleanField(default=True)
    soft_deleted = models.BooleanField(default=False)

    def _str_(self):
        return self.product_name
    
    

class Wishlist(models.Model):
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    product=models.ForeignKey(Product, on_delete=models.CASCADE)
    
# varient_category_choice =(
#     ('RC 18000','RC 18000'),
#     ('RC 25000','RC 25000'),
# )   
    
# class Varient(models.Model):
#     varient_name = models.CharField(max_length=200, unique=True)
#     varient_images = models.ImageField(upload_to='photos/products')
#     varient_category = models.CharField(max_length=200, choices= varient_category_choice)
#     product = models.ForeignKey(Product, on_delete=models.CASCADE)
#     # category = models.ForeignKey(Category, on_delete=models.CASCADE)
#     description = models.TextField(max_length=500, blank=True)
#     # price = models.IntegerField()
#     # quantity = models.IntegerField()
#     is_available = models.BooleanField(default=True)

#     def __str__(self):
#         return self.varient_name
    
    
    
# class Cart(models.Model):
#     cart_id=models.CharField(max_length=250,blank=True)
#     user=models.ForeignKey("account.Customuser", on_delete=models.CASCADE)
#     date_created=models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f'Cart for {self.user.username}'
    



# class CartItems(models.Model):
#     cart=models.ForeignKey("cart.Cart",on_delete=models.CASCADE)
#     product=models.ForeignKey("store.ProductImage",on_delete=models.CASCADE)
#     quantity=models.PositiveIntegerField(default=0)


#     def __str__(self) -> str:
#         return f'{self.product.product.product_name} -{self.quantity}'