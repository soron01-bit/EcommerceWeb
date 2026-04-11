from django.contrib import admin
from .models import Store, Product, ProductCertificate, Review, ProductImage

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ('uploaded_at',)

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'store', 'price', 'discount_percentage', 'stock', 'stock_status')
    list_filter = ('store', 'price', 'discount_percentage')
    search_fields = ('name', 'description')
    readonly_fields = ('stock_status',)
    inlines = [ProductImageInline]
    fieldsets = (
        ('Product Information', {
            'fields': ('store', 'name', 'description', 'image')
        }),
        ('Pricing & Inventory', {
            'fields': ('price', 'discount_percentage', 'stock', 'stock_status')
        }),
    )

admin.site.register(Store)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductCertificate)
admin.site.register(Review)
admin.site.register(ProductImage)
