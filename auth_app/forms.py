from django import forms
from .models import CustomUser
from crispy_forms.helper import FormHelper
from django.forms.widgets import EmailInput
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model


class CustomUserSignupForm(forms.ModelForm):
    # Sign up form for new users
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'required': True, 
            'pattern': "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", 
            'title': "Please enter a valid email address"
        })
    )

    first_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'required': True,
            'minlength': 3,
            'title': "First name must be at least 3 characters long."
        })
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'required': True,
            'minlength': 3,
            'title': "Last name must be at least 3 characters long."
        })
    )

    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'required': True,
            'minlength': 8,
            'title': "Password must be at least 8 characters long, include a mix of letters and numbers."
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'required': True,
            'minlength': 8,
            'title': "Please re-enter the password."
        })
    )

    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists")
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        
        if len(password1) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        if not any(char.isdigit() for char in password1):
            raise ValidationError("Password must contain at least one number.")
        if not any(char.isalpha() for char in password1):
            raise ValidationError("Password must contain at least one letter.")

        return password2

    def __init__(self, *args, **kwargs):
        super(CustomUserSignupForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)

User = get_user_model()

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.exclude(pk=self.instance.pk).filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username
    
    
class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email_address = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    message = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control'}))
