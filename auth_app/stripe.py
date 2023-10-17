# Django imports
from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

# Third-party imports
import json
import stripe

# App-specific imports
from auth_app.models import Address, CustomUser, Order, OrderItem
from tackle.models import Product, WebhookLog
from tackle.views import Cart



stripe.api_key = settings.STRIPE_SECRET_KEY


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    webhook_log = WebhookLog(
        payload=payload.decode('utf-8'),
        header=sig_header,
        status='received',
    )

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        webhook_log.event_type = event.type
    except ValueError:
        webhook_log.status = 'invalid payload'
        webhook_log.save()
        return JsonResponse({'status': 'invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        webhook_log.status = 'invalid signature'
        webhook_log.save()
        return JsonResponse({'status': 'invalid signature'}, status=400)

    handle_stripe_event(event, webhook_log)

    return JsonResponse({'status': 'success'})


def handle_stripe_event(event, webhook_log):
    if event.type == 'payment_intent.succeeded':
        payment_intent = event.data.object
        webhook_log.payment_intent_id = payment_intent.id
        try:
            order = Order.objects.get(payment_intent_id=payment_intent.id)
            order.payment_status = 'completed'
            order.status = 'paid'
            order.save()

            for order_item in order.items.all():
                product = order_item.product
                product.financial_status = 'sold'
                product.save()

            webhook_log.order = order
            webhook_log.status = 'success'
            webhook_log.save()
        except Order.DoesNotExist:
            webhook_log.status = 'order not found'
            webhook_log.save()

    elif event.type == 'payment_intent.payment_failed':
        payment_intent = event.data.object
        webhook_log.payment_intent_id = payment_intent.id
        try:
            order = Order.objects.get(payment_intent_id=payment_intent.id)
            order.payment_status = 'failed'
            order.status = 'failed'
            order.save()

            webhook_log.order = order
            webhook_log.status = 'payment failed'
            webhook_log.save()
        except Order.DoesNotExist:
            webhook_log.status = 'order not found'
            webhook_log.save()

    elif event.type == 'account.updated':
        account = event.data.object
        try:
            user = CustomUser.objects.get(stripe_account_id=account.id)
            
            if account.details_submitted:
                user.is_stripe_verified = True
                user.save()
                webhook_log.status = 'account verified'
            else:
                user.is_stripe_verified = False
                user.save()
                webhook_log.status = 'account updated but not verified'

        except CustomUser.DoesNotExist:
            webhook_log.status = 'user not found for Stripe account'
            webhook_log.save()

    elif event.type == 'charge.refund.updated':
        refund = event.data.object

        if refund.status == 'failed':
            webhook_log.payment_intent_id = refund.charge

            try:
                order = Order.objects.get(payment_intent_id=refund.charge)
                order.payment_status = 'rf'
                order.save()

                webhook_log.order = order
                webhook_log.status = 'refund failed'
                webhook_log.save()
            except Order.DoesNotExist:
                webhook_log.status = 'order not found'
                webhook_log.save()


@csrf_exempt
def handle_payment(request):
    payment_method_id = request.POST.get('payment_method')

    user = get_or_create_user(request)

    cart = Cart(request)
    total_amount = int((cart.get_total_price() + cart.get_shipping_total()) * 100)

    order = create_order(user, cart)

    billing_address, shipping_address = create_addresses(user, request, order)
    
    try:
        initiate_stripe_payment(user, total_amount, payment_method_id, order, cart)
        return JsonResponse({'success': True, 'redirect_url': reverse('home')})

    except stripe.error.StripeError as e:
        return JsonResponse({'error': str(e)})
    except Exception as e:
        return JsonResponse({'error': 'An unexpected error occurred: ' + str(e)})


def get_or_create_user(request):
    if request.user.is_authenticated:
        return request.user
    else:
        email = request.POST['email']
        try:
            return CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return CustomUser.objects.create_user(
                email=email,
                password=CustomUser.objects.make_random_password(),
                first_name=request.POST['first_name'],
                last_name=request.POST['last_name'],
                is_active=False,
                is_staff=False
            )


def create_order(user, cart):
    order = Order(
        user=user,
        product_cost=cart.get_total_price(),
        shipping_cost=cart.get_shipping_total(),
        total_amount=(cart.get_total_price() + cart.get_shipping_total()),
        payment_status='pending'
    )
    order.save()
    return order


def create_addresses(user, request, order):
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

    return billing_address, shipping_address


def initiate_stripe_payment(user, total_amount, payment_method_id, order, cart):
    payment_intent = stripe.PaymentIntent.create(
        amount=total_amount,
        currency='gbp',
        payment_method=payment_method_id,
        confirmation_method='manual',
        confirm=True,
        return_url="https://www.sellyourtackle.co.uk",
            metadata={
            'user_email': user.email,
            'user_first_name': user.first_name,
            'user_last_name': user.last_name
        }
    )

    order.payment_intent_id = payment_intent.id
    order.save()

    for item in cart:
        order_item = OrderItem.objects.create(
            order=order,
            product_id=item['product_id'],
            price=item['price'],
            quantity=item['quantity'],
            seller=item['product'].user
        )

        stripe.Transfer.create(
            amount=int(order.total_amount * 100),
            currency='gbp',
            destination=order_item.seller.stripe_account_id,
            metadata={
                'user_email': user.email,
                'user_first_name': user.first_name,
                'user_last_name': user.last_name
            }
        )

    cart.clear()


def create_stripe_express_account(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'User not authenticated'})

    try:
        account = stripe.Account.create(
          country="GB",
          type="express",
          business_type="individual",
          business_profile={
              "url": "https://www.sellyourtackle.co.uk",
              "product_description": "Selling fishing equipment on TackleTarts.",
              "mcc": "5941",
          },
          capabilities={
              "card_payments": {"requested": True},
              "transfers": {"requested": True}
          }
        )

        request.user.stripe_account_id = account.id
        request.user.save()

        account_link = stripe.AccountLink.create(
            account=account.id,
            refresh_url="https://www.sellyourtackle.co.uk/auth/reauth",
            return_url="https://www.sellyourtackle.co.uk/auth/wallet",
            type="account_onboarding"
        )

        return redirect(account_link.url)

    except stripe.error.StripeError as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def create_stripe_account_link(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'User not authenticated'})

    if not request.user.stripe_account_id:
        return JsonResponse({'status': 'error', 'message': 'Stripe account not found for user'})

    try:
        account_link = stripe.AccountLink.create(
            account=request.user.stripe_account_id,
            refresh_url="https://www.sellyourtackle.co.uk/auth/reauth",
            return_url="https://www.sellyourtackle.co.uk/auth/wallet",
            type="account_onboarding"
        )

        return JsonResponse({'status': 'success', 'url': account_link.url})

    except stripe.error.StripeError as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def handle_stripe_return(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'User not authenticated'})

    if not request.user.stripe_account_id:
        return JsonResponse({'status': 'error', 'message': 'Stripe account not found for user'})

    try:
        stripe_account = stripe.Account.retrieve(request.user.stripe_account_id)

        if stripe_account.details_submitted:
            return redirect('https://www.sellyourtackle.co.uk/auth/wallet')
        else:
            return redirect('some_setup_guide_url')

    except stripe.error.StripeError as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
