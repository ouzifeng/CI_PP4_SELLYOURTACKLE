from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from auth_app.models import CustomUser

class CustomAccountAdapter(DefaultAccountAdapter):

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        
        # Check if the user exists and is inactive, then make them active
        try:
            existing_user = CustomUser.objects.get(email=user.email)
            if not existing_user.is_active:
                existing_user.is_active = True
                existing_user.save()
        except CustomUser.DoesNotExist:
            pass

        return user

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

    def is_auto_signup_allowed(self, request, sociallogin):
        # Check if user exists
        user = sociallogin.user
        if user.id:  # User already exists, skip signup form
            return True
        if CustomUser.objects.filter(email=user.email).exists():
            # If a user exists with this email, we should link the social account to this user
            existing_user = CustomUser.objects.get(email=user.email)
            sociallogin.connect(request, existing_user)
            return True  # Skip the signup form
        return False  # Show the signup form