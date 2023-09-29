from sib_api_v3_sdk import SendSmtpEmail, SendSmtpEmailTo, ApiClient, Configuration, TransactionalEmailsApi
from django.conf import settings

def send_confirmation_email(to_email, confirmation_link):
    # Configure API key authorization: api-key
    configuration = Configuration()
    configuration.api_key['api-key'] = settings.SENDINBLUE_API_KEY


    api_instance = TransactionalEmailsApi(ApiClient(configuration))
    
    # Define the email recipients
    to = [SendSmtpEmailTo(email=to_email)]
    
    # Define the email content
    subject = "Confirm your email address"
    html_content = f"<p>Please click the link below to confirm your email:</p><a href='{confirmation_link}'>Confirm Email</a>"
    
    # Send the email
    email = SendSmtpEmail(to=to, subject=subject, html_content=html_content, sender=SendSmtpEmailTo(email="hello@sellyourtackle.co.uk"))
    try:
        # Send a transactional email
        api_response = api_instance.send_transac_email(email)
        print(api_response)
    except Exception as e:
        print("Exception when calling TransactionalEmailsApi->send_transac_email: %s\n" % e)
