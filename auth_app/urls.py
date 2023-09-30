from django.urls import path
from . import views
from .views import SignupView, CustomLoginView, ConfirmEmailView, LogoutView, ConfirmEmailPageView

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('confirm-email-link/', ConfirmEmailPageView.as_view(), name='confirm-email-link'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('confirm-email/<int:user_id>/<str:token>/', ConfirmEmailView.as_view(), name='confirm-email'),
] 

