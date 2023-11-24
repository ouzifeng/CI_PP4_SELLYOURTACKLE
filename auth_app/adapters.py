from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from auth_app.models import CustomUser


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Extends DefaultAccountAdapter to customize the user population process
    during social login. It activates existing users if they are not active.
    """
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        try:
            existing_user = CustomUser.objects.get(email=user.email)
            if not existing_user.is_active:
                existing_user.is_active = True
                existing_user.save()
        except CustomUser.DoesNotExist:
            pass

        return user


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Extends DefaultSocialAccountAdapter to customize the auto-signup
    process for social accounts. It allows auto-signup and connects existing
    users based on email.
    """
    def is_auto_signup_allowed(self, request, sociallogin):
        user = sociallogin.user
        if user.id:
            return True
        if CustomUser.objects.filter(email=user.email).exists():
            existing_user = CustomUser.objects.get(email=user.email)
            sociallogin.connect(request, existing_user)
            return True
        return False
