from django.contrib import admin
from .models import Store, Product, ProductCertificate, Review

admin.site.register(Store)
admin.site.register(Product)
admin.site.register(ProductCertificate)
admin.site.register(Review)
