from django.db import models
from django.contrib.auth.models import User

class Store(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='store', null=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=300)

    def __str__(self):
        return self.name

class Product(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    stock = models.IntegerField(default=0)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text='Discount percentage (0-100)')

    def __str__(self):
        return self.name
    
    @property
    def is_in_stock(self):
        return self.stock > 0
    
    @property
    def stock_status(self):
        if self.stock > 10:
            return 'In Stock'
        elif self.stock > 0:
            return 'Low Stock'
        else:
            return 'Out of Stock'
    
    @property
    def discounted_price(self):
        if self.discount_percentage > 0:
            discount_amount = self.price * (self.discount_percentage / 100)
            return self.price - discount_amount
        return self.price

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['uploaded_at']
    
    def __str__(self):
        return f"Image for {self.product.name}"

class ProductCertificate(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='certificate')
    title = models.CharField(max_length=250)
    validation_id = models.CharField(max_length=100)
    issued_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Certificate for {self.product.name}"

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField()
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} for {self.product.name}"

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.username}"
    
    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.all())
    
    def get_total_items(self):
        return sum(item.quantity for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1, blank=False, null=False)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} (x{self.quantity}) in {self.cart.user.username}'s cart"
    
    def get_total_price(self):
        # Use discounted price if discount is available
        return self.product.discounted_price * self.quantity


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=255, blank=True)
    default_address = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.username}"


class Order(models.Model):
    PAYMENT_METHOD_COD = 'COD'
    PAYMENT_METHOD_CARD = 'CARD'
    PAYMENT_METHOD_UPI = 'UPI'
    PAYMENT_METHOD_BANK = 'BANK'
    PAYMENT_METHOD_CHOICES = [
        (PAYMENT_METHOD_COD, 'Cash on Delivery'),
        (PAYMENT_METHOD_CARD, 'Card'),
        (PAYMENT_METHOD_UPI, 'UPI'),
        (PAYMENT_METHOD_BANK, 'Bank Transfer'),
    ]

    PAYMENT_STATUS_PENDING = 'PENDING'
    PAYMENT_STATUS_PAID = 'PAID'
    PAYMENT_STATUS_FAILED = 'FAILED'
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_STATUS_PENDING, 'Pending'),
        (PAYMENT_STATUS_PAID, 'Paid'),
        (PAYMENT_STATUS_FAILED, 'Failed'),
    ]

    STATUS_PENDING = 'PENDING'
    STATUS_SHIPPED = 'SHIPPED'
    STATUS_DELIVERED = 'DELIVERED'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_SHIPPED, 'Shipped'),
        (STATUS_DELIVERED, 'Delivered'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='orders')
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    address = models.TextField()
    location = models.CharField(max_length=255)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(
        max_length=10,
        choices=PAYMENT_STATUS_CHOICES,
        default=PAYMENT_STATUS_PENDING,
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} by {self.user.username} - {self.product.name}"
