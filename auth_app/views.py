from django.shortcuts import render, redirect
from .forms import CustomUserSignupForm
from django.contrib.auth import logout, login
from django.contrib.auth.views import LoginView
from .email import send_confirmation_email
from .models import EmailConfirmationToken, CustomUser
from django.http import HttpResponse
from uuid import uuid4
from django.views import View
from django.views.generic import RedirectView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from tackle.models import Product, ProductImage

class SignupView(View):

    def get(self, request, *args, **kwargs):
        form = CustomUserSignupForm()
        return render(request, 'signup.html', {'form': form})

    def post(self, request, *args, **kwargs):
        form = CustomUserSignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            
            email_prefix = user.email.split('@')[0]
            all_usernames = list(CustomUser.objects.values_list('username', flat=True))
            user.username = CustomUser.objects.generate_unique_username(email_prefix, all_usernames)
            
            user.save()
            
            token = uuid4()
            EmailConfirmationToken.objects.create(user=user, token=token)
            
            confirmation_link = f"http://localhost:8000/auth/confirm-email/{user.id}/{token}/"
            send_confirmation_email(user.email, confirmation_link, user.first_name)

            
            return redirect('confirm-email-link') 

        return render(request, 'signup.html', {'form': form})


class LogoutView(RedirectView):
    pattern_name = 'home'  

    def get(self, request, *args, **kwargs):
        logout(request)
        return super().get(request, *args, **kwargs)

class CustomLoginView(LoginView):
    template_name = 'login.html'
    
class ConfirmEmailPageView(View):
    template_name = 'confirm-email.html'
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
 
 
class ConfirmEmailView(View):

    def get(self, request, user_id, token, *args, **kwargs):
        try:
            token_obj = EmailConfirmationToken.objects.get(user__id=user_id, token=token)
        except EmailConfirmationToken.DoesNotExist:
            return HttpResponse("Invalid token or user ID", status=400)

        user = token_obj.user
        if not user.is_active:
            user.is_active = True
            user.save()
            token_obj.delete()  # Optionally delete the token after it's used

            # Log the user in
            login(request, user)

            return redirect('home')  # Redirect to the homepage

        return HttpResponse("This email has already been confirmed.")


@method_decorator(login_required, name='dispatch')    
class MyAccount(View):
    template_name = 'my-account.html'
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)    
    
@method_decorator(login_required, name='dispatch')    
class Buying(View):
    template_name = 'buying.html'
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)       
    
@method_decorator(login_required, name='dispatch')    
class Selling(View):
    template_name = 'selling.html'
    
    def get(self, request, *args, **kwargs):
        user_products = Product.objects.filter(user=request.user)
        product_images = {}
        
        for product in user_products:
            first_image = ProductImage.objects.filter(product=product).first()
            if first_image:
                product_images[product.id] = first_image.image.url
        
        context = {
            'user_products': user_products,
            'product_images': product_images
        }
        return render(request, self.template_name, context)
