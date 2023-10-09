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
            phone_number_collection={
                'enabled': True,
            },
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

