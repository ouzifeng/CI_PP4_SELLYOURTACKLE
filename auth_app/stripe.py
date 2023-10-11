from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import stripe
from .models import Order
from django.conf import settings
from auth_app.models import CustomUser, Order, OrderItem, Address
from tackle.views import Cart
from django.db import transaction

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
        # Update the order status to "paid" or equivalent in your database
        try:
            order = Order.objects.get(payment_intent_id=payment_intent.id)
            order.payment_status = 'paid'
            order.save()
            # Additional post-payment logic, like sending a confirmation email, can be added here
        except Order.DoesNotExist:
            # Handle cases where the order is not found
            pass

    elif event.type == 'payment_intent.payment_failed':
        payment_intent = event.data.object
        # Update the order status to "failed"
        try:
            order = Order.objects.get(payment_intent_id=payment_intent.id)
            order.payment_status = 'failed'
            order.save()
            # Additional logic for handling payment failures, like notifying the user, can be added here
        except Order.DoesNotExist:
            # Handle cases where the order is not found
            pass

    return JsonResponse({'status': 'success'})


@csrf_exempt
def handle_payment(request):
    # Extract the payment method from POST data
    payment_method_id = request.POST.get('payment_method')

    try:
        # Determine the user for the order
        if request.user.is_authenticated:
            user = request.user
        else:
            email = request.POST['email']
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                user = CustomUser.objects.create_user(
                    email=email,
                    password=CustomUser.objects.make_random_password(),
                    first_name=request.POST['first_name'],
                    last_name=request.POST['last_name'],
                    is_active=False,
                    is_staff=False
                )


        cart = Cart(request)
        total_amount = int((cart.get_total_price() + cart.get_shipping_total()) * 100)  # Convert to cents

        # Confirm the payment with Stripe
        payment_intent = stripe.PaymentIntent.create(
            amount=total_amount,
            currency='gbp',
            payment_method=payment_method_id,
            confirmation_method='manual',
            confirm=True,
            return_url="https://www.sellyourtackle.co.uk",
            metadata={
                'user_email': email
            },
            shipping={  # Add shipping info if necessary
                'name': f"{request.POST['first_name']} {request.POST['last_name']}",
                'address': {
                    'line1': request.POST['shipping_address_line1'],
                    'line2': request.POST.get('shipping_address_line2', ""),
                    'city': request.POST['shipping_city'],
                    'state': request.POST['shipping_state'],
                    'postal_code': request.POST['shipping_postal_code'],
                    'country': 'GB',  # Assuming GB, adjust if needed
                }
            }
        )



        with transaction.atomic():
            # Create an order instance
            order = Order(
                user=user,
                product_cost=cart.get_total_price(),
                shipping_cost=cart.get_shipping_total(),
                total_amount=cart.get_total_price() + cart.get_shipping_total(),
                payment_status='pending',
                payment_intent_id=payment_intent.id
            )
            order.save()

            # Save billing address
            billing_address = Address(
                user=user,
                address_type='billing',
                first_name=request.POST['first_name'],
                last_name=request.POST['last_name'],
                email=request.POST['email'],
                phone_number=request.POST.get('phone_number', ""),
                address_line1=request.POST['billing_address_line1'],
                address_line2=request.POST.get('billing_address_line2', ""),
                city=request.POST['billing_city'],
                state=request.POST['billing_state'],
                postal_code=request.POST['billing_postal_code']
            )
            billing_address.save()
            order.billing_address = billing_address

            # Save shipping address
            if request.POST.get('use_different_shipping_address'):
                shipping_address = Address(
                    user=user,
                    address_type='shipping',
                    first_name=request.POST.get('shipping_first_name', request.POST['first_name']),
                    last_name=request.POST.get('shipping_last_name', request.POST['last_name']),
                    address_line1=request.POST['shipping_address_line1'],
                    address_line2=request.POST.get('shipping_address_line2', ""),
                    city=request.POST['shipping_city'],
                    state=request.POST['shipping_state'],
                    postal_code=request.POST['shipping_postal_code']
                )
                shipping_address.save()
                order.shipping_address = shipping_address
            else:
                order.shipping_address = billing_address

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


