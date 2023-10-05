from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import stripe

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
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
