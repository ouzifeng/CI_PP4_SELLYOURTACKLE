from django import forms


class CheckoutForm(forms.Form):
    """
    Builds the checkout form
    """
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

    payment_method = forms.CharField(widget=forms.HiddenInput())

    use_different_shipping_address = forms.BooleanField(
        required=False,
        initial=False,
        label="Is shipping address different from billing address?"
    )


class ContactSellerForm(forms.Form):
    """
    Builds the conact form on the contact us page
    """
    subject = forms.CharField(max_length=100)
    message = forms.CharField(widget=forms.Textarea)
