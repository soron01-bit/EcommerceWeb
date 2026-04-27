from django.contrib import admin
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'product',
        'quantity',
        'total_price',
        'location',
        'payment_method',
        'payment_status',
        'status',
        'created_at',
    )
    list_filter = ('payment_method', 'payment_status', 'status', 'created_at')
    search_fields = ('user__username', 'product__name', 'location', 'address')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    list_select_related = ('user', 'product')
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
