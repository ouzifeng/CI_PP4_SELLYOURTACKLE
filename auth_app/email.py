from mailjet_rest import Client
from django.conf import settings
from django.core.mail import send_mail
from .models import OrderItem, Order


def send_confirmation_email(to_email, confirmation_link, first_name):
    """
    Sends an email to a user with a link to confirm their email address.
    The email includes a personalized greeting and a confirmation link.
    """
    subject = "Confirm your email address"
    from_email = "hello@sellyourtackle.co.uk"

    html_content = f"""
    <html>
        <body>
            <p>Hi {first_name},</p>
            <p>Please confirm your Sell Your Tackle account by clicking
            <a href="{confirmation_link}">this link</a>.</p>
            <p>Thanks,</p>
            <p>Sell Your Tackle Team</p>
        </body>
    </html>
    """

    send_mail(
        subject,
        '',
        from_email,
        [to_email],
        html_message=html_content
    )


def send_reset_password_email(to_email, reset_link, first_name):
    """
    Sends a password reset email to a user. This email contains a
    personalized message with a link to reset the password. It also advises
    users to ignore the email if they didn't request a password reset.
    """
    subject = "Reset your password"
    from_email = "hello@sellyourtackle.co.uk"

    html_content = f"""
    <html>
        <body>
            <p>Hi {first_name},</p>
            <p>Click <a href="{reset_link}">here</a> to reset
            your password.</p>
            <p>If you didn't request a password reset,
            please ignore this email.</p>
            <p>Thanks,</p>
            <p>Sell Your Tackle Team</p>
        </body>
    </html>
    """

    send_mail(
        subject,
        '',
        from_email,
        [to_email],
        html_message=html_content
    )


def send_order_confirmation_email(order):
    """
    Sends an email to the buyer with a confirmation
    of the order
    """
    buyer_email = order.user.email
    buyer_first_name = order.user.first_name

    order_items = OrderItem.objects.filter(order=order)
    items_details_list = []
    for item in order_items:
        product_name = item.product.name
        quantity = item.quantity
        total_price = item.get_total_item_price()
        item_detail = f"{product_name} (x{quantity}) - £{total_price}"
        items_details_list.append(item_detail)

    items_details = "\n".join(items_details_list)

    total_cost = order.total_amount
    shipping_address = order.shipping_address
    address_line1 = shipping_address.address_line1
    city = shipping_address.city
    state = shipping_address.state
    postal_code = shipping_address.postal_code
    shipping_details = f"{address_line1}, {city}, {state}, {postal_code}"

    subject = "Your Sell Your Tackle Order Confirmation"
    html_content = f"""
    <html>
        <body>
            <p>Hi {buyer_first_name},</p>
            <p>Thank you for your purchase. Here are the details:</p>
            <p>{items_details}</p>
            <p>Total Cost: £{total_cost}</p>
            <p>Shipping Address: {shipping_details}</p>
            <p>If you have any questions, please contact us.</p>
            <p>Thanks,</p>
            <p>The Sell Your Tackle Team</p>
        </body>
    </html>
    """

    send_mail(
        subject,
        '',
        'hello@sellyourtackle.co.uk',
        [buyer_email],
        html_message=html_content
    )


def send_product_sold_email(order_item):
    seller_email = order_item.product.user.email
    seller_first_name = order_item.product.user.first_name
    product_name = order_item.product.name
    quantity_sold = order_item.quantity
    total_price = order_item.get_total_item_price_with_shipping()

    subject = "Product Sold Notification"
    html_content = f"""
    <html>
        <body>
            <p>Hi {seller_first_name},</p>
            <p>Congratulations! Your '{product_name}' has been sold.</p>
            <p>Quantity Sold: {quantity_sold}</p>
            <p>Total Price: £{total_price}</p>
            <p>Please login to view the shipping details</p>
            <p>www.sellyourtackle.co.uk/auth/selling</p>
            <p>Thanks,</p>
            <p>The Sell Your Tackle Team</p>
        </body>
    </html>
    """

    send_mail(
        subject,
        '',
        'hello@sellyourtackle.co.uk',
        [seller_email],
        html_message=html_content
    )
