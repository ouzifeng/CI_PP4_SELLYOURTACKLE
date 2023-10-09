from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Order
from django.conf import settings
from auth_app.models import CustomUser, Order, OrderItem
from tackle.views import Cart
import stripe, logging


logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    logger.info(f"Received webhook. Signature: {sig_header}, Payload: {payload}")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.error("Error: Invalid payload received.")
        return JsonResponse({'status': 'invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        logger.error("Error: Signature verification failed.")
        return JsonResponse({'status': 'invalid signature'}, status=400)

    # Handle the event
    if event.type == 'checkout.session.completed':
        session = event.data.object
        client_reference_id = session.client_reference_id
        
        logger.info(f"Handling checkout.session.completed for client_reference_id: {client_reference_id}")
        
        try:
            order = Order.objects.get(id=client_reference_id)
            logger.info(f"Found order with ID {client_reference_id}. Current PaymentIntentID: {order.payment_intent_id}")

            # Update the order with the PaymentIntent ID
            order.payment_intent_id = session.payment_intent
            order.payment_status = 'completed'
            order.status = 'paid'  
            order.save()

            logger.info(f"Order updated. New PaymentIntentID: {order.payment_intent_id}")

        except Order.DoesNotExist:
            logger.error(f"Order with ID {client_reference_id} not found in database!")
            return JsonResponse({'status': 'error'}, status=400)

    elif event.type == 'payment_intent.payment_failed':
        payment_intent = event.data.object
        related_session = stripe.checkout.Session.list(payment_intent=payment_intent.id)[0]
        client_reference_id = related_session.client_reference_id

        try:
            order = Order.objects.get(id=client_reference_id)
            order.payment_status = 'failed'
            order.save()
            # Notify the user about the failed payment here
            logger.info(f"Payment failed for order with ID {client_reference_id}. PaymentIntentID: {payment_intent.id}")

        except Order.DoesNotExist:
            logger.error(f"Order with ID {client_reference_id} not found in database!")
            return JsonResponse({'status': 'error'}, status=400)

    else:
        logger.info(f"Received unhandled event type: {event.type}")

    return JsonResponse({'status': 'success'})

@csrf_exempt
def handle_payment(request, order_id):
    # Retrieve the order
    order = Order.objects.get(pk=order_id)
    
    # Extract cart details
    cart = Cart(request)
    
    # Calculate the total amount
    total_amount = int(order.total_amount * 100)  # Convert to cents
    
    # Prepare line items for Stripe Checkout
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

        # Shipping line item
        shipping_line_item = {
            'price_data': {
                'currency': 'gbp',
                'product_data': {
                    'name': f"Shipping for {product.name}",
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
            client_reference_id=str(order.id),  # Using the order's unique ID
            shipping_address_collection={
                'allowed_countries': ['GB'],
            },
            payment_intent_data={
                'description': f'Order {order.id}'
            }
        )
        # Return the session ID to the frontend
        return JsonResponse({'session_id': session.id})

    except stripe.error.StripeError as e:
        return JsonResponse({'error': str(e)})

