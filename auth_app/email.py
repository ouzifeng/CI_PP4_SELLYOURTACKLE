from mailjet_rest import Client
from django.conf import settings
from django.core.mail import send_mail


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
