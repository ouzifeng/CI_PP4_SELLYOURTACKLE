from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit

class CheckoutForm(forms.Form):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=False)

    # Billing Address
    billing_address_line1 = forms.CharField(max_length=255, required=True)
    billing_address_line2 = forms.CharField(max_length=255, required=False)
    billing_city = forms.CharField(max_length=100, required=True)
    billing_state = forms.CharField(max_length=100, required=True)
    billing_postal_code = forms.CharField(max_length=10, required=True)

    # Shipping Address
    shipping_first_name = forms.CharField(max_length=100, required=True)
    shipping_last_name = forms.CharField(max_length=100, required=True)
    shipping_address_line1 = forms.CharField(max_length=255, required=True)
    shipping_address_line2 = forms.CharField(max_length=255, required=False)
    shipping_city = forms.CharField(max_length=100, required=True)
    shipping_state = forms.CharField(max_length=100, required=True)
    shipping_postal_code = forms.CharField(max_length=10, required=True)

    payment_method = forms.CharField(widget=forms.HiddenInput())  # Stripe Payment Method ID

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'billing_address_line1',
            'billing_address_line2',
            'billing_city',
            'billing_state',
            'billing_postal_code',
            'shipping_first_name',
            'shipping_last_name',
            'shipping_address_line1',
            'shipping_address_line2',
            'shipping_city',
            'shipping_state',
            'shipping_postal_code',
            'payment_method',
            Submit('submit', 'Place Order')
        )
