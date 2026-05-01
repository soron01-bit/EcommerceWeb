from django.contrib import admin
from .models import (
    Store, Product, ProductImage, ProductCertificate,
    Review, Cart, CartItem, UserProfile, Order,
)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductCertificateInline(admin.StackedInline):
    model = ProductCertificate
    extra = 0
    max_num = 1


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'location')
    search_fields = ('name', 'owner__username', 'location')
    list_filter = ('location',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'store', 'size_type', 'price', 'discount_percentage',
        'discounted_price_display', 'stock', 'stock_status',
    )
    list_filter = ('store', 'size_type', 'discount_percentage')
    search_fields = ('name', 'description', 'store__name')
    list_editable = ('price', 'discount_percentage', 'stock', 'size_type')
    inlines = [ProductImageInline, ProductCertificateInline]

    @admin.display(description='Sale Price')
    def discounted_price_display(self, obj):
        return f'₹{obj.discounted_price:.2f}'

    @admin.display(description='Status')
    def stock_status(self, obj):
        return obj.stock_status


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('product__name',)


@admin.register(ProductCertificate)
class ProductCertificateAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'title', 'validation_id', 'issued_at')
    search_fields = ('product__name', 'title', 'validation_id')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__name', 'user__username', 'text')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'updated_at')
    search_fields = ('user__username',)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'product', 'quantity', 'added_at')
    search_fields = ('cart__user__username', 'product__name')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'phone_number', 'location', 'updated_at')
    search_fields = ('user__username', 'phone_number', 'location')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'product', 'size', 'quantity', 'total_price',
        'location', 'payment_method', 'payment_status', 'status', 'created_at',
    )
    list_filter = ('size', 'payment_method', 'payment_status', 'status', 'created_at')
    search_fields = ('user__username', 'product__name', 'size', 'location', 'address')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    list_select_related = ('user', 'product')
    list_editable = ('payment_status', 'status')
    actions = ['cancel_orders']

    @admin.action(description='Cancel selected orders and restore stock')
    def cancel_orders(self, request, queryset):
        cancelled_count = 0
        for order in queryset:
            if order.status == Order.STATUS_PENDING:
                order.status = Order.STATUS_CANCELLED
                order.save(update_fields=['status'])

                # Restore stock
                order.product.stock += order.quantity
                order.product.save(update_fields=['stock'])
                cancelled_count += 1

        self.message_user(
            request,
            f'{cancelled_count} orders were successfully cancelled and stock restored.',
        )
