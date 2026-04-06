from django.contrib import admin
from .models import Store, Product, ProductCertificate, Review

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'store', 'price', 'stock', 'stock_status')
    list_filter = ('store', 'price')
    search_fields = ('name', 'description')
    readonly_fields = ('stock_status',)
    fieldsets = (
        ('Product Information', {
            'fields': ('store', 'name', 'description', 'image')
        }),
        ('Pricing & Inventory', {
            'fields': ('price', 'stock', 'stock_status')
        }),
    )

admin.site.register(Store)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductCertificate)
admin.site.register(Review)
