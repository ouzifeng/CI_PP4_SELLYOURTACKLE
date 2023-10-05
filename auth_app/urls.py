from django.urls import path
from . import views
from .views import SignupView, CustomLoginView, ConfirmEmailView, LogoutView, ConfirmEmailPageView, MyAccount, Buying, Selling, CheckoutSuccessView
from .stripe import stripe_webhook

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('confirm-email-link/', ConfirmEmailPageView.as_view(), name='confirm-email-link'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('confirm-email/<int:user_id>/<str:token>/', ConfirmEmailView.as_view(), name='confirm-email'),
    path('my-account/', MyAccount.as_view(), name='my-account'),
    path('buying/', Buying.as_view(), name='buying'),
    path('selling/', Selling.as_view(), name='selling'),
    path('stripe_webhook/', stripe_webhook, name='stripe_webhook'),    
    path('checkout_success/', CheckoutSuccessView.as_view(), name='checkout_success'),
] 

