from mailjet_rest import Client
from django.conf import settings

def send_confirmation_email(to_email, confirmation_link, first_name):
    api_key = settings.MAILJET_API_KEY       # Assuming you've added these to your Django settings
    api_secret = settings.MAILJET_SECRET_KEY 
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')
    
    data = {
        'Messages': [{
            "From": {"Email": "hello@sellyourtackle.co.uk", "Name": "Sell Your Tackle"},
            "To": [{"Email": to_email, "Name": first_name}],
            "TemplateID": 11261190, 
            "TemplateLanguage": True,
            "Subject": "Confirm your email address",
            "Variables": {
                "first_name": first_name,
                "confirmation_link": confirmation_link
            }
        }]
    }
    
    result = mailjet.send.create(data=data)
    print(result.status_code, result.json())
