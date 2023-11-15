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
from django.core.mail import send_mail

# Local application/library specific imports
from .forms import CustomUserSignupForm, UserUpdateForm, ContactForm, PasswordResetRequestForm, SetNewPasswordForm
from .email import send_confirmation_email, send_reset_password_email
from .models import (
    EmailConfirmationToken,
    CustomUser,
    Order,
    OrderItem,
    Address,
    PasswordResetToken
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
        user.set_password(form.cleaned_data['password1']) 
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


class PrivacyView(View):
    """Renders the about us page."""
    template_name = 'privacy.html'
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
    
class TermsView(View):
    """Renders the about us page."""
    template_name = 'terms.html'
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)    
    
class AboutUsView(View):
    """Renders the privacy page."""
    template_name = 'about.html'
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)    
    
class ContactUsView(View):
    template_name = 'contact.html'
    
    def get(self, request, *args, **kwargs):
        form = ContactForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = ContactForm(request.POST)
        if form.is_valid():
            # Use a verified sender email
            from_email = 'hello@sellyourtackle.co.uk'
            
            # Include the user's email in the subject or message
            subject = "Contact form submission from " + form.cleaned_data['name'] + " (" + form.cleaned_data['email_address'] + ")"
            message = form.cleaned_data['message']
            
            send_mail(subject, message, from_email, ['hello@sellyourtackle.co.uk'])

            messages.success(request, "Email sent successfully!")
            return redirect('contact')
        return render(request, self.template_name, {'form': form})

    

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
class Buying(View):
    """Displays the user's orders."""
    template_name = 'buying.html'
    
    def get(self, request, *args, **kwargs):
        user_orders = Order.objects.filter(user=request.user).prefetch_related('items').order_by('-created_at')
        order_product_images = self._get_order_product_images(user_orders)
        paginator = Paginator(user_orders, 10)
        page = request.GET.get('page')
        orders_on_page = paginator.get_page(page)
        return render(request, self.template_name, {
            'user_orders': orders_on_page,
            'order_product_images': order_product_images
        })


    def _get_order_product_images(self, orders):
        """Returns the first image for each product in the orders."""
        order_product_images = {}
        for order in orders:
            for item in order.items.all():
                product = item.product
                first_image = ProductImage.objects.filter(product=product).first()
                if first_image:
                    order_product_images[product.id] = first_image.image.url          
        return order_product_images


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

class ResetPasswordView(View):
    template_name = 'reset-password.html'

    def get(self, request, *args, **kwargs):
        form = PasswordResetRequestForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = PasswordResetRequestForm(request.POST)
        
        if form.is_valid():
            email = form.cleaned_data['email']
            user = CustomUser.objects.filter(email=email).first()
            
            if user:
                # Create token and send email
                token = PasswordResetToken.objects.create(user=user)
                reset_link = f"https://www.sellyourtackle.co.uk/auth/reset-password/{token.token}/"
                send_reset_password_email(user.email, reset_link, user.first_name)  # Uncomment this
                return redirect('home')  # A page to inform the user that a reset link has been sent
            else:
                form.add_error('email', 'Email not found.')
        else:
            print(form.errors)

        return render(request, self.template_name, {'form': form})

class ResetPasswordConfirmView(View):
    template_name = 'reset-password-confirm.html'
    
    def get(self, request, token, *args, **kwargs):
        try:
            reset_token = PasswordResetToken.objects.get(token=token)
            if reset_token.is_expired:
                messages.error(request, "The reset link has expired. Please request a new one.")
                return redirect('reset-password')
        except PasswordResetToken.DoesNotExist:
            messages.error(request, "Invalid reset token. Please request a new one.")
            return redirect('reset-password')
        
        form = SetNewPasswordForm()
        return render(request, self.template_name, {'form': form, 'token': token})

    def post(self, request, token, *args, **kwargs):
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password1']
            try:
                reset_token = PasswordResetToken.objects.get(token=token)
                user = reset_token.user
                user.set_password(password)
                user.save()
                reset_token.delete()
                messages.success(request, "Password updated successfully!")
                return redirect('login')
            except PasswordResetToken.DoesNotExist:
                messages.error(request, "Invalid reset token. Please request a new one.")
                return redirect('reset-password')
        return render(request, self.template_name, {'form': form, 'token': token})
