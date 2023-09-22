from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
 

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


class CustomUser(AbstractBaseUser, PermissionsMixin):
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="customuser_groups",
        related_query_name="customuser",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="customuser_permissions",
        related_query_name="customuser",
    )
    
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    
    # Mangopay-related fields
    mangopay_user_id = models.CharField(max_length=255, blank=True, null=True)
    mangopay_user_type = models.CharField(max_length=20, choices=[('NATURAL', 'Natural'), ('LEGAL', 'Legal')], blank=True, null=True)
    mangopay_wallet_id = models.CharField(max_length=255, blank=True, null=True)
    kyc_status = models.CharField(max_length=50, blank=True, null=True)
    bank_account_id = models.CharField(max_length=255, blank=True, null=True)
    
    # For legal users
    legal_rep_first_name = models.CharField(max_length=255, blank=True, null=True)
    legal_rep_last_name = models.CharField(max_length=255, blank=True, null=True)
    # ... (add more fields for legal representative info as needed)
    
    # Other fields
    # profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    # ... (any other fields specific to user profiles)
