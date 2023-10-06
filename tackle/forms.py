from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field
from crispy_forms.bootstrap import PrependedText

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
    shipping_first_name = forms.CharField(max_length=100, required=False)
    shipping_last_name = forms.CharField(max_length=100, required=False)
    shipping_address_line1 = forms.CharField(max_length=255, required=False)
    shipping_address_line2 = forms.CharField(max_length=255, required=False)
    shipping_city = forms.CharField(max_length=100, required=False)
    shipping_state = forms.CharField(max_length=100, required=False)
    shipping_postal_code = forms.CharField(max_length=10, required=False)

    payment_method = forms.CharField(widget=forms.HiddenInput())  # Stripe Payment Method ID
    
    use_different_shipping_address = forms.BooleanField(
    required=False,
    initial=False,
    label="Is shipping address different from billing address?"
    )
    

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
        Row(
            Column('first_name', css_class='form-group col-md-6 mb-0'),
            Column('last_name', css_class='form-group col-md-6 mb-0'),
            css_class='form-row'
        ),
        'email',
        'phone_number',
        Row(
            Column('billing_address_line1', css_class='form-group col-md-6 mb-0'),
            Column('billing_address_line2', css_class='form-group col-md-6 mb-0'),
            css_class='form-row'
        ),
        Row(
            Column('billing_city', css_class='form-group col-md-6 mb-0'),
            Column('billing_state', css_class='form-group col-md-6 mb-0'),
            css_class='form-row'
        ),
        'billing_postal_code',
        'use_different_shipping_address',
        Field('shipping_first_name', css_class='shipping-field'),
        Field('shipping_last_name', css_class='shipping-field'),
        Row(
            Column(Field('shipping_address_line1', css_class='shipping-field'), css_class='form-group col-md-6 mb-0'),
            Column(Field('shipping_address_line2', css_class='shipping-field'), css_class='form-group col-md-6 mb-0'),
            css_class='form-row'
        ),
        Row(
            Column(Field('shipping_city', css_class='shipping-field'), css_class='form-group col-md-6 mb-0'),
            Column(Field('shipping_state', css_class='shipping-field'), css_class='form-group col-md-6 mb-0'),
            css_class='form-row'
        ),
        Field('shipping_postal_code', css_class='shipping-field'),
        'payment_method',
        Submit('submit', 'Place Order')
    )

