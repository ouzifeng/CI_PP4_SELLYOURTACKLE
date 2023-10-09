from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Order
from django.conf import settings
from auth_app.models import CustomUser, Order, OrderItem
from tackle.views import Cart
import stripe


stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    print("Received a webhook request")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        print("Error: Invalid payload")
        return JsonResponse({'status': 'invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        print("Error: Invalid signature")
        return JsonResponse({'status': 'invalid signature'}, status=400)

    # Handle the 'checkout.session.completed' event
    if event.type == 'checkout.session.completed':
        print("Handling checkout.session.completed event")

        session = event.data.object
        client_reference_id = session.client_reference_id

        email = session['customer_details']['email']
        print(f"User email from the payload: {email}")
        full_name = session['customer_details']['name']
        first_name, *middle_names, last_name = full_name.split()
        first_name = " ".join([first_name] + middle_names)

        # Get or create user
        email_prefix = email.split('@')[0]
        all_usernames = list(CustomUser.objects.values_list('username', flat=True))
        username = CustomUser.objects.generate_unique_username(email_prefix, all_usernames)

        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={
                'username': username,  # Use the generated unique username
                'first_name': first_name,
                'last_name': last_name,
                'is_active': False,
                'is_staff': False
            }
        )
        
        if created:
            print(f"Created a new user with email: {email}")
        else:
            print(f"Found an existing user with email: {email}")

        try:
            order = Order.objects.get(id=client_reference_id)

            order.user = user
            order.payment_intent_id = session['payment_intent']
            order.payment_status = 'completed'
            order.status = 'paid'  
            order.save()

            print(f"Updated order with ID: {client_reference_id}")

        except Order.DoesNotExist:
            print(f"Error: Order with ID {client_reference_id} does not exist")
            return JsonResponse({'status': 'error'}, status=400)

    elif event.type == 'payment_intent.payment_failed':
        print("Handling payment_intent.payment_failed event")

        payment_intent = event.data.object
        related_session = stripe.checkout.Session.list(payment_intent=payment_intent.id)[0]
        client_reference_id = related_session.client_reference_id

        try:
            order = Order.objects.get(id=client_reference_id)
            order.payment_status = 'failed'
            order.save()

            print(f"Updated payment status to 'failed' for order with ID: {client_reference_id}")

        except Order.DoesNotExist:
            print(f"Error: Order with ID {client_reference_id} does not exist")
            return JsonResponse({'status': 'error'}, status=400)

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

