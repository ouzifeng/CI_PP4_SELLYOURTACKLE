import os
from unittest.mock import patch, Mock
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import CustomUser, Order, EmailConfirmationToken
from .forms import (CustomUserSignupForm, ContactForm,
                    PasswordResetRequestForm, SetNewPasswordForm)
from .views import ConfirmEmailView, Buying
import uuid

User = get_user_model()


class CustomUserModelTest(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='testuser@example.com', password='password123'
        )

    def test_user_creation(self):
        self.assertEqual(self.user.email, 'testuser@example.com')


class CustomUserSignupFormTest(TestCase):

    def test_signup_form_valid(self):
        form_data = {
            'email': 'validuser@example.com',
            'password1': 'validpassword123',
            'password2': 'validpassword123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        form = CustomUserSignupForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_signup_form_invalid(self):
        form_data = {
            'email': 'validuser@example.com',
            'password1': 'validpassword123',
            'password2': 'validpassword123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        form = CustomUserSignupForm(data=form_data)
        self.assertFalse(form.is_valid())


class ContactFormTest(TestCase):

    def test_contact_form_valid(self):
        form_data = {
            'name': 'Test Name',
            'email_address': 'test@example.com',
            'message': 'Test message'
        }
        form = ContactForm(data=form_data)
        self.assertTrue(form.is_valid())


class PasswordResetRequestFormTest(TestCase):

    def test_password_reset_request_form_valid(self):
        form_data = {'email': 'user@example.com'}
        form = PasswordResetRequestForm(data=form_data)
        self.assertTrue(form.is_valid())


class SetNewPasswordFormTest(TestCase):

    def test_set_new_password_form_valid(self):
        form_data = {
            'password1': 'newpassword123',
            'password2': 'newpassword123'
        }
        form = SetNewPasswordForm(data=form_data)
        self.assertTrue(form.is_valid())


class ConfirmEmailViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='password123',
            is_active=False
        )
        self.token = '3e65560a-187d-44d1-af64-500162fe305c'

    def test_confirm_email(self):
        token = EmailConfirmationToken.objects.create(
            user=self.user, token=self.token
        )
        response = self.client.get(
            reverse('confirm-email', args=[self.user.id, self.token])
        )
        self.user.refresh_from_db()

        self.assertTrue(self.user.is_active)
        self.assertEqual(response.status_code, 302)


class BuyingViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='testbuyer@example.com', password='password123'
        )
        self.client.login(
            email='testbuyer@example.com', password='password123'
        )

    def test_buying_view(self):
        response = self.client.get(reverse('buying'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'buying.html')


# Stripe Integration Tests
@patch('stripe.AccountLink.create')
@patch('stripe.Account.retrieve')
class StripeIntegrationTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='teststripe@example.com',
            password='password123',
            stripe_account_id='acct_123'
        )

    def test_handle_stripe_return(self, mock_retrieve, mock_account_link):
        mock_account_link.return_value = Mock(url='test_url')
        mock_retrieve.return_value = Mock(details_submitted=True)
        self.client.login(
            email='teststripe@example.com', password='password123'
        )
        response = self.client.get(reverse('handle_stripe_return'))
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_stripe_verified)
