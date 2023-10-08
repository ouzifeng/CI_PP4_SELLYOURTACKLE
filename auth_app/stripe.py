from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import stripe
from .models import Order
from django.conf import settings
from auth_app.models import CustomUser, Order, OrderItem
from tackle.views import Cart


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
        return JsonResponse({'status': 'invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        return JsonResponse({'status': 'invalid signature'}, status=400)

    # Handle the event
    if event.type == 'payment_intent.succeeded':
        payment_intent = event.data.object
        # Locate the order using the payment_intent ID
        order = Order.objects.get(payment_intent_id=payment_intent.id)
        order.payment_status = 'completed'
        order.status = 'paid'  
        order.save()

    elif event.type == 'payment_intent.payment_failed':
        payment_intent = event.data.object
        order = Order.objects.get(payment_intent_id=payment_intent.id)
        order.payment_status = 'failed'
        order.save()
        # Notify the user about the failed payment here

    return JsonResponse({'status': 'success'})


@csrf_exempt
def handle_payment(request, order_id):
    # Retrieve the order
    order = Order.objects.get(pk=order_id)
    
    # Extract cart details
    cart = Cart(request)
    
    # Prepare line items for Stripe Checkout using price_data
    line_items = []
    for item in cart:
        product = item['product']

        # Product line item
        product_line_item = {
            'price_data': {
                'currency': 'gbp',
                'product_data': {
                    'name': product.name,
                },
                'unit_amount': int(item['price'] * 100),  # Convert to cents
            },
            'quantity': item['quantity'],
        }
        line_items.append(product_line_item)

        # Shipping line item for the product
        shipping_line_item = {
            'price_data': {
                'currency': 'gbp',
                'product_data': {
                    'name': f"Shipping",
                },
                'unit_amount': int(item['shipping_cost'] * 100), 
            },
            'quantity': item['quantity'],
        }
        line_items.append(shipping_line_item)

    try:
        # Create a Stripe Checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=['card', 'paypal'],
            line_items=line_items,
            mode='payment',
            success_url='https://www.sellyourtackle.co.uk/',  
            cancel_url='https://www.sellyourtackle.co.uk/', 
            client_reference_id=order_id,  # Associate this session with the order
            shipping_address_collection={
                'allowed_countries': ['GB'],
            }
        )

        # Return the session ID to the frontend
        return JsonResponse({'session_id': session.id})

    except stripe.error.StripeError as e:
        return JsonResponse({'error': str(e)})
