from django.urls import path

# Authentication views
from .views import (
    SignupView,
    CustomLoginView,
    ConfirmEmailView,
    LogoutView,
    ConfirmEmailPageView,
    AboutUsView,
    ContactUsView,
    PrivacyView,
    TermsView,
    ResetPasswordView,
    ResetPasswordConfirmView
)

# User actions/views
from .views import Buying, Selling, WalletView

# Stripe related views
from .stripe import (
    stripe_webhook,
    handle_payment,
    create_stripe_express_account,
    create_stripe_account_link,
    handle_stripe_return
)

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path(
        'confirm-email-link/', ConfirmEmailPageView.as_view(),
        name='confirm-email-link'
        ),
    path('login/', CustomLoginView.as_view(), name='login'),
    path(
        'confirm-email/<int:user_id>/<str:token>/',
        ConfirmEmailView.as_view(), name='confirm-email'
    ),
    path('buying/', Buying.as_view(), name='buying'),
    path('selling/', Selling.as_view(), name='selling'),
    path('stripe_webhook/', stripe_webhook, name='stripe_webhook'),
    path('handle_payment/', handle_payment, name='handle_payment'),
    path('wallet/', WalletView.as_view(), name='wallet'),
    path(
        'create_stripe_express_account/', create_stripe_express_account,
        name='create_stripe_express_account'
        ),
    path(
        'create_stripe_account_link/', create_stripe_account_link,
        name='create_stripe_account_link'
        ),
    path(
        'handle_stripe_return/', handle_stripe_return,
        name='handle_stripe_return'
        ),
    path('about-us/', AboutUsView.as_view(), name='about-us'),
    path('contact/', ContactUsView.as_view(), name='contact'),
    path('privacy/', PrivacyView.as_view(), name='privacy'),
    path('terms/', TermsView.as_view(), name='terms'),
    path(
        'reset-password/', ResetPasswordView.as_view(),
        name='reset-password'
        ),
    path(
        'reset-password/<str:token>/', ResetPasswordConfirmView.as_view(),
        name='reset-password-confirm'
        ),

]
