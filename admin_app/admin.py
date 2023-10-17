from django.contrib import admin, messages
from tackle.models import Product
from auth_app.models import CustomUser, Order
import stripe

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product_cost', 'status', 'payment_status', 'created_at')
    list_filter = ('status', 'payment_status', 'created_at')
    search_fields = ('user__email', 'status', 'payment_intent_id')

    def save_model(self, request, obj, form, change):
        # If the order's status has been changed to "refunded"
        if 'status' in form.changed_data and obj.status == 'refunded':
            # Refund the order using Stripe's API
            try:
                stripe.Refund.create(payment_intent=obj.payment_intent_id)
                obj.payment_status = 'refunded'
                messages.success(request, f"Order {obj.id} has been marked as refunded.")
            except stripe.error.StripeError as e:
                messages.error(request, f"Stripe error for Order {obj.id}: {str(e)}")
                return  # Do not save the model if refund failed
        super().save_model(request, obj, form, change)


admin.site.register(Order, OrderAdmin)

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'date_joined', 'last_login')
    search_fields = ('email',)
    
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'financial_status', 'created_at')
    list_filter = ('financial_status',)
    search_fields = ('name', 'description', 'financial_status')    