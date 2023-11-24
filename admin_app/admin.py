from django.contrib import admin, messages
from tackle.models import Product
from auth_app.models import CustomUser, Order
import stripe


class OrderAdmin(admin.ModelAdmin):
    """
    Customizes the Django admin interface for Order models,
    including list display, filtering options, and search
    capabilities.
    """
    list_display = (
        'id',
        'user',
        'product_cost',
        'status',
        'payment_status',
        'created_at'
    )
    list_filter = ('status', 'payment_status', 'created_at')
    search_fields = ('user__email', 'status', 'payment_intent_id')

    def save_model(self, request, obj, form, change):
        if 'status' in form.changed_data and obj.status == 'refunded':
            try:
                stripe.Refund.create(payment_intent=obj.payment_intent_id)
                obj.payment_status = 'refunded'
                order_id = f"Order {obj.id}"
                order_refund_msg = f"{order_id} has been marked as refunded."
                messages.success(request, order_refund_msg)
            except stripe.error.StripeError as e:
                error_msg = f"Stripe error for Order {obj.id}: {str(e)}"
                messages.error(request, error_msg)
        super().save_model(request, obj, form, change)


admin.site.register(Order, OrderAdmin)


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    """
    Configures the Django admin interface for CustomUser models,
    specifically setting up list display and search functionality.
    """

    list_display = ('email', 'date_joined', 'last_login')
    search_fields = ('email',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Tailors the Django admin interface for Product models,
    including list display, filter options, and search fields.
    """
    list_display = ('name', 'price', 'financial_status', 'created_at')
    list_filter = ('financial_status',)
    search_fields = ('name', 'description', 'financial_status')
