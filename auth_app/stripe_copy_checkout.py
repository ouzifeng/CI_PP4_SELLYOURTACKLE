from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Order
from django.conf import settings
from auth_app.models import CustomUser, Order, OrderItem
from tackle.views import Cart
import stripe
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
        return JsonResponse({'status': 'invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        return JsonResponse({'status': 'invalid signature'}, status=400)

    if event.type == 'checkout.session.completed':
        session = event.data.object
        client_reference_id = session.client_reference_id
        email = session.customer_details.email
        full_name = session.customer_details.name
        first_name, *middle_names, last_name = full_name.split()
        first_name = " ".join([first_name] + middle_names)

        try:
            with transaction.atomic():
                user, created = CustomUser.objects.get_or_create(
                    email=email,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'is_active': False,
                        'is_staff': False
                    }
                )
                order = Order.objects.get(id=client_reference_id)
                order.user = user
                order.payment_intent_id = session.payment_intent
                order.payment_status = 'completed'
                order.status = 'paid'

                # Extract shipping address and create/update Address object
                shipping_details = session.get('shipping_details')
                if shipping_details:
                    shipping_address, _ = Address.objects.get_or_create(
                        user=user,
                        address_type='shipping',
                        defaults={
                            'first_name': first_name,
                            'last_name': last_name,
                            'address_line1': shipping_details['address']['line1'],
                            'address_line2': shipping_details['address']['line2'],
                            'city': shipping_details['address']['city'],
                            'state': shipping_details['address']['state'],
                            'postal_code': shipping_details['address']['postal_code'],
                            'phone_number': shipping_details['phone'] if 'phone' in shipping_details else None
                        }
                    )
                    order.shipping_address = shipping_address

                # Extract billing address and create/update Address object
                billing_details = session.get('customer_details')
                if billing_details and billing_details.get('address'):
                    billing_address, _ = Address.objects.get_or_create(
                        user=user,
                        address_type='billing',
                        defaults={
                            'first_name': first_name,
                            'last_name': last_name,
                            'address_line1': billing_details['address']['line1'],
                            'address_line2': billing_details['address']['line2'],
                            'city': billing_details['address']['city'],
                            'state': billing_details['address']['state'],
                            'postal_code': billing_details['address']['postal_code'],
                            'phone_number': billing_details['phone'] if 'phone' in billing_details else None
                        }
                    )
                    order.billing_address = billing_address

                order.save()

        except CustomUser.DoesNotExist:
            return JsonResponse({'status': 'error'}, status=400)
        except Order.DoesNotExist:
            return JsonResponse({'status': 'error'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error'}, status=500)


    elif event.type == 'payment_intent.payment_failed':
        payment_intent = event.data.object

        try:
            related_sessions = stripe.checkout.Session.list(payment_intent=payment_intent.id)
            related_session = related_sessions.data[0] if related_sessions.data else None
            client_reference_id = related_session.client_reference_id

            if "last_payment_error" in payment_intent and \
            "payment_method" in payment_intent["last_payment_error"] and \
            "billing_details" in payment_intent["last_payment_error"]["payment_method"]:
                email = payment_intent["last_payment_error"]["payment_method"]["billing_details"]["email"]
            else:
                email = None

            if "shipping" in payment_intent:
                full_name = payment_intent["shipping"]["name"]
            else:
                full_name = None
            first_name, *middle_names, last_name = full_name.split()
            first_name = " ".join([first_name] + middle_names)

            with transaction.atomic():
                user, created = CustomUser.objects.get_or_create(
                    email=email,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'is_active': False,
                        'is_staff': False
                    }
                )
                order = Order.objects.get(id=client_reference_id)
                order.user = user
                order.payment_intent_id = payment_intent.id
                order.payment_status = 'failed'
                order.status = 'failed'
                order.save()

        except CustomUser.DoesNotExist:
            return JsonResponse({'status': 'error'}, status=400)
        except Order.DoesNotExist:
            return JsonResponse({'status': 'error'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error'}, status=500)

    return JsonResponse({'status': 'success'})




@csrf_exempt
def handle_payment(request):
    data = json.loads(request.body)
    payment_method_id = data['payment_method_id']

    try:
        cart = Cart(request)
        total_amount = int(cart.get_total_price() * 100)  # Convert to cents

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
                'is_staff': False
            }
        )
        if created:  # Only set a password if the user was just created
            user.set_unusable_password()  # This makes the password unusable, which means the user cannot log in until a password is set
            user.save()
    
    
        with transaction.atomic():
            # Create a 'pending' order instance
            order = Order(
                user=user,
                product_cost=cart.get_total_price(),
                total_amount=cart.get_total_price(),
                payment_status='pending',
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

        # Confirm the payment with Stripe
        payment_intent = stripe.PaymentIntent.create(
            amount=total_amount,
            currency='gbp',
            payment_method=payment_method_id,
            confirmation_method='manual',
            confirm=True
        )

        return JsonResponse({'success': True})

    except stripe.error.StripeError as e:
        return JsonResponse({'error': str(e)})
