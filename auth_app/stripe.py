from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import stripe
from .models import Order, OrderItem
from tackle.models import WebhookLog, Product
from django.conf import settings
from auth_app.models import CustomUser, Order, OrderItem, Address
from tackle.views import Cart
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse


stripe.api_key = settings.STRIPE_SECRET_KEY


@csrf_exempt
def stripe_webhook(request):
    """
    View for handling Stripe webhook events. It logs the webhook event,
    verifies the signature, and processes different Stripe event types
    like 'payment_intent.succeeded', 'payment_intent.payment_failed',
    and 'account.updated'.
    """
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    event = None

    webhook_log = WebhookLog(
        payload=payload.decode("utf-8"),
        header=sig_header,
        status="received",
    )

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        webhook_log.event_type = event.type
    except ValueError:
        webhook_log.status = "invalid payload"
        webhook_log.save()
        return JsonResponse({"status": "invalid payload"}, status=400)
    except stripe.error.SignatureVerificationError:
        webhook_log.status = "invalid signature"
        webhook_log.save()
        return JsonResponse({"status": "invalid signature"}, status=400)

    if event.type == "payment_intent.succeeded":
        payment_intent = event.data.object
        webhook_log.payment_intent_id = payment_intent.id
        try:
            order = Order.objects.get(payment_intent_id=payment_intent.id)
            order.payment_status = "completed"
            order.status = "paid"
            order.save()

            for order_item in order.items.all():
                product = order_item.product
                product.financial_status = "sold"
                product.save()

            webhook_log.order = order
            webhook_log.status = "success"
            webhook_log.save()

        except Order.DoesNotExist:
            webhook_log.status = "order not found"
            webhook_log.save()

    elif event.type == "payment_intent.payment_failed":
        payment_intent = event.data.object
        webhook_log.payment_intent_id = payment_intent.id
        try:
            order = Order.objects.get(payment_intent_id=payment_intent.id)
            order.payment_status = "failed"
            order.status = "failed"
            order.save()

            webhook_log.order = order
            webhook_log.status = "payment failed"
            webhook_log.save()

        except Order.DoesNotExist:
            webhook_log.status = "order not found"
            webhook_log.save()

    elif event.type == "account.updated":
        account = event.data.object
        try:
            user = CustomUser.objects.get(stripe_account_id=account.id)

            if account.details_submitted:
                user.is_stripe_verified = True
                user.save()
                webhook_log.status = "account verified"
            else:
                user.is_stripe_verified = False
                user.save()
                webhook_log.status = "account updated but not verified"

        except CustomUser.DoesNotExist:
            webhook_log.status = "user not found for Stripe account"

        webhook_log.save()

    return JsonResponse({"status": "success"})


@csrf_exempt
def handle_payment(request):
    """
    View for handling the payment process. It creates a Stripe payment
    intent and handles the entire checkout process, including order creation,
    address handling, and Stripe transfer initiation.
    """
    payment_method_id = request.POST.get("payment_method")

    try:
        if request.user.is_authenticated:
            user = request.user
        else:
            email = request.POST["email"]
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                user = CustomUser.objects.create_user(
                    email=email,
                    password=CustomUser.objects.make_random_password(),
                    first_name=request.POST["first_name"],
                    last_name=request.POST["last_name"],
                    is_active=False,
                    is_staff=False,
                )

        cart = Cart(request)
        total_amount = int(cart.get_total_price() + cart.get_shipping_total())
        total_amount *= 100

        order = Order(
            user=user,
            product_cost=cart.get_total_price(),
            shipping_cost=cart.get_shipping_total(),
            total_amount=(cart.get_total_price() + cart.get_shipping_total()),
            payment_status="pending",
        )
        order.save()

        billing_address = Address(
            user=user,
            address_type="billing",
            first_name=request.POST["first_name"],
            last_name=request.POST["last_name"],
            email=request.POST["email"],
            phone_number=request.POST.get("phone_number", ""),
            address_line1=request.POST["billing_address_line1"],
            address_line2=request.POST.get("billing_address_line2", ""),
            city=request.POST["billing_city"],
            state=request.POST["billing_state"],
            postal_code=request.POST["billing_postal_code"],
        )
        billing_address.save()
        order.billing_address = billing_address

        if request.POST.get("use_different_shipping_address"):
            shipping_address = Address(
                user=user,
                address_type="shipping",
                first_name=request.POST.get(
                    "shipping_first_name", request.POST["first_name"]
                ),
                last_name=request.POST.get(
                    "shipping_last_name", request.POST["last_name"]
                ),
                address_line1=request.POST["shipping_address_line1"],
                address_line2=request.POST.get("shipping_address_line2", ""),
                city=request.POST["shipping_city"],
                state=request.POST["shipping_state"],
                postal_code=request.POST["shipping_postal_code"],
            )
            shipping_address.save()
            order.shipping_address = shipping_address
        else:
            order.shipping_address = billing_address
        order.save()

        payment_intent = stripe.PaymentIntent.create(
            amount=total_amount,
            currency="gbp",
            payment_method=payment_method_id,
            confirmation_method="manual",
            confirm=True,
            return_url="https://www.sellyourtackle.co.uk",
            metadata={
                "user_email": user.email,
                "user_first_name": user.first_name,
                "user_last_name": user.last_name,
            },
        )

        order.payment_intent_id = payment_intent.id
        order.save()

        for item in cart:
            commission_amount = (
                item["price"] * item["quantity"] * settings.STRIPE_COMMISSION_RATE
            )
            seller_amount = int(
                item["price"]
                * item["quantity"]
                * 100
                * (1 - settings.STRIPE_COMMISSION_RATE)
            )

            order_item = OrderItem.objects.create(
                order=order,
                product_id=item["product_id"],
                price=item["price"],
                quantity=item["quantity"],
                seller=item["product"].user,
                commission=commission_amount,
            )

            stripe.Transfer.create(
                amount=seller_amount,
                currency="gbp",
                destination=order_item.seller.stripe_account_id,
                metadata={
                    "user_email": user.email,
                    "user_first_name": user.first_name,
                    "user_last_name": user.last_name,
                },
            )

        cart.clear()

        redirect_url = reverse("order-confirmation", args=[order.pk])
        return JsonResponse({"success": True, "redirect_url": redirect_url})

    except stripe.error.StripeError as e:
        return JsonResponse({"error": str(e)})

    except Exception as e:
        error_message = "An unexpected error occurred: " + str(e)
        return JsonResponse({"error": error_message})


def create_stripe_express_account(request):
    """
    View for creating a new Stripe Express account for the user.
    It checks user authentication, creates a Stripe account, and
    redirects to the Stripe account setup page.
    """
    if not request.user.is_authenticated:
        response_data = {"status": "error", "message": "Not authenticated"}
        return JsonResponse(response_data)

    try:
        account = stripe.Account.create(
            country="GB",
            type="express",
            business_type="individual",
            business_profile={
                "url": "https://www.sellyourtackle.co.uk",
                "product_description": "Sell fishing equipment on TackleTarts.",
                "mcc": "5941",
            },
            capabilities={
                "card_payments": {"requested": True},
                "transfers": {"requested": True},
            },
        )

        request.user.stripe_account_id = account.id
        request.user.save()
        account_link = stripe.AccountLink.create(
            account=account.id,
            refresh_url="https://www.sellyourtackle.co.uk/auth/reauth",
            return_url="https://www.sellyourtackle.co.uk/list-product/",
            type="account_onboarding",
        )

        return redirect(account_link.url)

    except stripe.error.StripeError as e:
        return JsonResponse({"status": "error", "message": str(e)})


def create_stripe_account_link(request):
    """
    View for creating a Stripe account link for existing users.
    It ensures user authentication and generates a Stripe account
    link for the user's account onboarding.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"status": "error", "message": "Unauthenticated"})

    if not request.user.stripe_account_id:
        error_message = "Stripe account not found for user"
        response_data = {"status": "error", "message": error_message}
        return JsonResponse(response_data)

    try:
        account_link = stripe.AccountLink.create(
            account=request.user.stripe_account_id,
            refresh_url="https://www.sellyourtackle.co.uk/auth/reauth",
            return_url="https://www.sellyourtackle.co.uk/auth/wallet",
            type="account_onboarding",
        )

        return JsonResponse({"status": "success", "url": account_link.url})

    except stripe.error.StripeError as e:
        return JsonResponse({"status": "error", "message": str(e)})


def handle_stripe_return(request):
    """
    View for handling the return from Stripe account setup.
    It checks the user's authentication and Stripe account details,
    verifies if the account setup is completed, and redirects
    to appropriate pages based on the Stripe account status.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"status": "error", "message": "Unauthenticated"})

    if not request.user.stripe_account_id:
        error_message = "Stripe account not found for user"
        response_data = {"status": "error", "message": error_message}
        return JsonResponse(response_data)

    try:
        stripe_account_id = request.user.stripe_account_id
        stripe_account = stripe.Account.retrieve(stripe_account_id)

        if stripe_account.details_submitted:
            request.user.is_stripe_verified = True
            request.user.save()
            return redirect("https://www.sellyourtackle.co.uk/list-product/")
        else:
            return redirect("some_setup_guide_url")

    except stripe.error.StripeError as e:
        return JsonResponse({"status": "error", "message": str(e)})
