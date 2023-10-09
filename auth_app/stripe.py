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

        # Extract email and name from the payload
        email = session.customer_details.email
        full_name = session.customer_details.name
        first_name, *middle_names, last_name = full_name.split()
        first_name = " ".join([first_name] + middle_names)

        print("Webhook triggered for checkout.session.completed")
        print(f"Email from payload: {email}")
        print(f"Client reference ID: {client_reference_id}")

        try:
            with transaction.atomic():
                print("Inside transaction block")

                # Get or create user
                print("Attempting to get or create user")
                user, created = CustomUser.objects.get_or_create(
                    email=email,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'is_active': False,
                        'is_staff': False
                    }
                )

                if created:
                    print(f"User with email {email} created")
                else:
                    print(f"User with email {email} already exists")

                # Fetch the order
                print("Attempting to fetch order")
                order = Order.objects.get(id=client_reference_id)
                print(f"Fetched order with ID {client_reference_id}")

                # Attach the user to the order
                print("Associating user with the order")
                order.user = user

                # Update the order with the PaymentIntent ID
                print("Updating order's payment details")
                order.payment_intent_id = session.payment_intent
                order.payment_status = 'completed'
                order.status = 'paid'
                print("Saving order")
                order.save()

            print(f"Order {client_reference_id} associated with user {email}")

        except CustomUser.DoesNotExist:
            print(f"No user found with email: {email}")
            return JsonResponse({'status': 'error'}, status=400)
        except Order.DoesNotExist:
            print(f"Order with ID {client_reference_id} does not exist")
            return JsonResponse({'status': 'error'}, status=400)
        except Exception as e:
            print(f"Unexpected error occurred: {str(e)}")
            return JsonResponse({'status': 'error'}, status=500)


    elif event.type == 'payment_intent.payment_failed':
        payment_intent = event.data.object
        print("Webhook triggered for payment_intent.payment_failed")
        print(f"Payment intent ID: {payment_intent.id}")

        try:
            # Fetch the related session using the payment intent
            print("Fetching related session for the payment intent")
            related_sessions = stripe.checkout.Session.list(payment_intent=payment_intent.id)
            related_session = related_sessions.data[0] if related_sessions.data else None
            client_reference_id = related_session.client_reference_id
            print(f"Client reference ID from related session: {client_reference_id}")

            # Extract email and name from the related session
            email = related_session.customer_details.email
            full_name = related_session.customer_details.name
            first_name, *middle_names, last_name = full_name.split()
            first_name = " ".join([first_name] + middle_names)
            print(f"Email from related session: {email}")

            with transaction.atomic():
                # Get or create user
                print("Attempting to get or create user")
                user, created = CustomUser.objects.get_or_create(
                    email=email,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'is_active': False,
                        'is_staff': False
                    }
                )

                if created:
                    print(f"User with email {email} created")
                else:
                    print(f"User with email {email} already exists")

                # Fetch the order and update its status
                print("Attempting to fetch order")
                order = Order.objects.get(id=client_reference_id)
                print(f"Fetched order with ID {client_reference_id}")

                # Attach the user to the order
                print("Associating user with the order")
                order.user = user

                order.payment_status = 'failed'
                print("Updating order's payment status to 'failed'")
                order.save()
                print("Order saved successfully")

        except CustomUser.DoesNotExist:
            print(f"No user found with email: {email}")
            return JsonResponse({'status': 'error'}, status=400)
        except Order.DoesNotExist:
            print(f"Order with ID {client_reference_id} does not exist")
            return JsonResponse({'status': 'error'}, status=400)
        except Exception as e:
            print(f"Unexpected error occurred: {str(e)}")
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

