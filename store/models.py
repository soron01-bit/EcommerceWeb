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

    def __str__(self):
        return self.name

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
