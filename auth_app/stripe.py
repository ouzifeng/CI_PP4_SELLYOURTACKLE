from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import stripe
from .models import Order
from django.conf import settings


stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        # Invalid payload
        return JsonResponse({'status': 'invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return JsonResponse({'status': 'invalid signature'}, status=400)

    # Handle the event
    if event.type == 'payment_intent.succeeded':
        payment_intent = event.data.object
        # Handle post-payment logic here (e.g., update database, send email)
    elif event.type == 'payment_intent.payment_failed':
        payment_intent = event.data.object
        # Handle payment failures here (e.g., notify the user, retry payment)

    return JsonResponse({'status': 'success'})

def handle_payment(request):
    data = json.loads(request.body)
    payment_method_id = data['payment_method_id']
    
    try:
        cart = Cart(request)
        total_amount = int(cart.get_total_price() * 100)  # Convert to cents
        
        # Confirm the payment
        payment_intent = stripe.PaymentIntent.create(
            amount=total_amount,
            currency='gbp',
            payment_method=payment_method_id,
            confirmation_method='manual',
            confirm=True
        )

        # Assuming you've also passed customer details in the request
        customer_data = data['customer']
        
        # Create an order instance
        order = Order(
            first_name = customer_data['first_name'],
            last_name = customer_data['last_name'],
            email = customer_data['email'],
            phone_number = customer_data['phone_number'],
            billing_address_line1 = customer_data['billing_address_line1'],
            billing_address_line2 = customer_data['billing_address_line2'],
            billing_city = customer_data['billing_city'],
            billing_state = customer_data['billing_state'],
            billing_postal_code = customer_data['billing_postal_code'],
            shipping_first_name = customer_data['shipping_first_name'],
            shipping_last_name = customer_data['shipping_last_name'],
            shipping_address_line1 = customer_data['shipping_address_line1'],
            shipping_address_line2 = customer_data['shipping_address_line2'],
            shipping_city = customer_data['shipping_city'],
            shipping_state = customer_data['shipping_state'],
            shipping_postal_code = customer_data['shipping_postal_code'],
            total_cost = cart.get_total_price(),
            payment_status = 'completed',
            stripe_payment_intent_id = payment_intent.id
        )
        order.save()

        # Save order items. Assuming you have an OrderItem model and product_id in cart items
        for item in cart:
            OrderItem.objects.create(
                order=order,
                product_id=item['product_id'],
                price=item['price'],
                quantity=item['quantity']
            )
        
        # Clear the cart after successful order placement
        cart.clear()

        return JsonResponse({'success': True})

    except stripe.error.StripeError as e:
        return JsonResponse({'error': str(e)})