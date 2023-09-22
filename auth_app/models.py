from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        
        # Generate a unique username based on email prefix
        email_prefix = email.split('@')[0]
        all_usernames = CustomUser.objects.values_list('username', flat=True)
        username = self.generate_unique_username(email_prefix, all_usernames)
        
        user.username = username
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

    def generate_unique_username(self, email_prefix, existing_users):
        username = email_prefix
        counter = 1
        while username in existing_users:
            username = f"{email_prefix}{counter}"
            counter += 1
        return username
