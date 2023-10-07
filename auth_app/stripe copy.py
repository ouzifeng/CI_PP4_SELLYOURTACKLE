from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import stripe
from .models import Order
from django.conf import settings
from auth_app.models import CustomUser, Order, OrderItem

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

@csrf_exempt
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

        # Determine the user based on authentication and email existence
        if request.user.is_authenticated:
            user = request.user
        else:
            email = data['customer']['email']
            user, created = CustomUser.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': data['customer']['first_name'],
                    'last_name': data['customer']['last_name'],
                    'is_active': False,
                    'password': CustomUser.objects.make_random_password()
                }
            )

        # Create an order instance
        order = Order(
            user=user,
            product_cost=cart.get_total_price(),
            total_amount=cart.get_total_price(),
            payment_status='completed',
            stripe_payment_intent_id=payment_intent.id
        )
        order.save()

        # Save order items
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
