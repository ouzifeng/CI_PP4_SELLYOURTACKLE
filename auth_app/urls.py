from django.urls import path
from . import views
from .views import SignupView, CustomLoginView, ConfirmEmailView, LogoutView, ConfirmEmailPageView, MyAccount, Buying, Selling, WalletView
from .stripe import stripe_webhook, handle_payment, connect_stripe, stripe_redirect

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
    path('handle_payment/', handle_payment, name='handle_payment'),
    path('wallet/', WalletView.as_view(), name='wallet'),
    path('connect_stripe/', connect_stripe, name='connect_stripe'),
    path('stripe_redirect/', stripe_redirect, name='stripe_redirect'),
]

