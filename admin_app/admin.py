from django.contrib import admin, messages
from tackle.models import Product
from auth_app.models import CustomUser, Order

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product_cost', 'status', 'payment_status', 'created_at')
    list_filter = ('status', 'payment_status', 'created_at')
    search_fields = ('user__email', 'status', 'payment_intent_id')
    
    actions = ['make_refunded']

    def make_refunded(self, request, queryset):
        # Loop through the selected orders in the admin
        for order in queryset:
            # Refund the order using Stripe's API
            try:
                stripe.Refund.create(payment_intent=order.payment_intent_id)
                order.status = 'refunded'
                order.payment_status = 'refunded'
                order.save()
                self.message_user(request, f"Order {order.id} has been marked as refunded.")
            except stripe.error.StripeError as e:
                self.message_user(request, f"Stripe error for Order {order.id}: {str(e)}", level=messages.ERROR)

    make_refunded.short_description = "Mark selected orders as Refunded"

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