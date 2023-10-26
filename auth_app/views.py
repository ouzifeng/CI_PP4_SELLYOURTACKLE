# Standard library imports
from uuid import uuid4

# Third-party imports
from django.shortcuts import render, redirect
from django.contrib.auth import logout, login
from django.contrib.auth.views import LoginView
from django.http import HttpResponse
from django.views import View
from django.views.generic import RedirectView, TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages

# Local application/library specific imports
from .forms import CustomUserSignupForm, UserUpdateForm
from .email import send_confirmation_email
from .models import (
    EmailConfirmationToken,
    CustomUser,
    Order,
    OrderItem,
    Address
)
from tackle.models import Product, ProductImage


class SignupView(View):
    """Handles user registration."""

    def get(self, request, *args, **kwargs):
        """Renders the signup form."""
        form = CustomUserSignupForm()
        return render(request, 'signup.html', {'form': form})

    def post(self, request, *args, **kwargs):
        """Processes the signup form submission."""
        form = CustomUserSignupForm(request.POST)
        if form.is_valid():
            user = self._create_inactive_user(form)
            self._send_confirmation_email(user)
            return redirect('confirm-email-link')
        
        return render(request, 'signup.html', {'form': form, 'errors': form.errors})

    def _create_inactive_user(self, form):
        """Creates an inactive user and returns it."""
        user = form.save(commit=False)
        user.is_active = False
        email_prefix = user.email.split('@')[0]
        all_usernames = list(CustomUser.objects.values_list('username', flat=True))
        user.username = CustomUser.objects.generate_unique_username(email_prefix)
        user.save()
        token = uuid4()
        EmailConfirmationToken.objects.create(user=user, token=token)
        return user

    def _send_confirmation_email(self, user):
        """Sends a confirmation email to the user."""
        token = EmailConfirmationToken.objects.get(user=user).token
        confirmation_link = f"https://www.sellyourtackle.co.uk/auth/confirm-email/{user.id}/{token}/"
        send_confirmation_email(user.email, confirmation_link, user.first_name)


class LogoutView(RedirectView):
    """Handles user logout."""
    pattern_name = 'home'  

    def get(self, request, *args, **kwargs):
        logout(request)
        return super().get(request, *args, **kwargs)


class CustomLoginView(LoginView):
    """Custom login view."""
    template_name = 'login.html'


@method_decorator(login_required, name='dispatch')
class WalletView(TemplateView):
    template_name = 'wallet.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['balance'] = user.balance
        context['form'] = UserUpdateForm(instance=user)
        
        # Fetching addresses
        billing_address = Address.objects.filter(user=user, address_type='billing').first()
        shipping_address = Address.objects.filter(user=user, address_type='shipping').first()

        context['billing_address'] = billing_address
        context['shipping_address'] = shipping_address
        
        return context
    
        
    def post(self, request, *args, **kwargs):
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Username updated successfully!")
            return redirect('wallet')
        else:
            context = self.get_context_data(**kwargs)
            context['form'] = form
            return render(request, self.template_name, context)


class AboutUsView(View):
    """Renders the about us page."""
    template_name = 'about.html'
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
    
class ContactUsView(View):
    """Renders the contact us page."""
    template_name = 'contact.html'
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)    
    

class ConfirmEmailPageView(View):
    """Renders the email confirmation page."""
    template_name = 'confirm-email.html'
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)


class ConfirmEmailView(View):
    """Handles email confirmation logic."""

    def get(self, request, user_id, token, *args, **kwargs):
        try:
            token_obj = EmailConfirmationToken.objects.get(user__id=user_id, token=token)
        except EmailConfirmationToken.DoesNotExist:
            return HttpResponse("Invalid token or user ID", status=400)

        user = token_obj.user
        if not user.is_active:
            user.is_active = True
            user.save()
            token_obj.delete() 
            login(request, user)
            messages.success(request, 'Your account has been activated successfully.')
            return redirect('home')

        return HttpResponse("This email has already been confirmed.")


@method_decorator(login_required, name='dispatch')
class MyAccount(View):
    """Renders the user's account page."""
    template_name = 'my-account.html'
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)


@method_decorator(login_required, name='dispatch')
class Buying(View):
    """Displays the user's orders."""
    template_name = 'buying.html'
    
    def get(self, request, *args, **kwargs):
        user_orders = Order.objects.filter(user=request.user).prefetch_related('items')
        paginator = Paginator(user_orders, 10)
        page = request.GET.get('page')
        orders_on_page = paginator.get_page(page)
        return render(request, self.template_name, {'user_orders': orders_on_page})


@method_decorator(login_required, name='dispatch')
class Selling(View):
    """Displays the products that the user is selling."""
    template_name = 'selling.html'
    
    def get(self, request, *args, **kwargs):
        user_products = Product.objects.filter(user=request.user)
        product_images = self._get_product_images(user_products)
        return render(request, self.template_name, {
            'user_products': user_products,
            'product_images': product_images
        })

    def _get_product_images(self, products):
        """Returns the first image for each product."""
        product_images = {}
        for product in products:
            first_image = ProductImage.objects.filter(product=product).first()
            if first_image:
                product_images[product.id] = first_image.image.url
        return product_images
