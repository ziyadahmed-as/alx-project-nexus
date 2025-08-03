import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication"""
    
    def create_user(self, email, username=None, password=None, **extra_fields):
        if not email:
            raise ValueError(_('Users must have an email address'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, username=username or email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMIN)
        extra_fields.setdefault('is_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, username, password, **extra_fields)


class User(AbstractUser):
    """Custom user model without spatial fields"""
    
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', _('Admin')
        CUSTOMER = 'CUSTOMER', _('Customer')
        VENDOR = 'VENDOR', _('Vendor')
        VENDOR_STAFF = 'VENDOR_STAFF', _('Vendor Staff')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, error_messages={'unique': _('Email already exists')})
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone format: '+999999999'")
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    last_active = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['email']), models.Index(fields=['role'])]

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Role.ADMIN
            self.is_verified = True
        super().save(*args, **kwargs)


class VendorProfile(models.Model):
    """Vendor profile without spatial business location"""
    
    class VerificationStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        VERIFIED = 'VERIFIED', _('Verified')
        REJECTED = 'REJECTED', _('Rejected')
        SUSPENDED = 'SUSPENDED', _('Suspended')

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='vendor_profile'
    )
    business_name = models.CharField(max_length=100)
    business_address = models.OneToOneField(
        'Address',
        on_delete=models.CASCADE,
        related_name='vendor_location',
        null=True,
        blank=True
    )
    # Changed from spatial to simple CharField
    business_location = models.CharField(max_length=255, null=True, blank=True)
    business_description = models.TextField(blank=True, null=True)
    business_email = models.EmailField()
    business_phone = models.CharField(max_length=20)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    store_logo = models.ImageField(upload_to='vendor_logos/')
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Vendor Profile')
        indexes = [models.Index(fields=['business_location'])]

    def __str__(self):
        return f"{self.business_name}"

    def save(self, *args, **kwargs):
        """Sync business location with address if exists"""
        if self.business_address and self.business_address.location:
            self.business_location = self.business_address.location
        super().save(*args, **kwargs)


class Address(models.Model):
    """Address model without spatial fields"""
    
    class AddressType(models.TextChoices):
        HOME = 'HOME', _('Home')
        BUSINESS = 'BUSINESS', _('Business')
        SHIPPING = 'SHIPPING', _('Shipping')
        BILLING = 'BILLING', _('Billing')

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='addresses'
    )
    address_type = models.CharField(
        max_length=10,
        choices=AddressType.choices,
        default=AddressType.HOME
    )
    recipient_name = models.CharField(max_length=100)
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    # Changed from spatial to simple CharField
    location = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Address')
        ordering = ['-is_default', 'user']
        indexes = [models.Index(fields=['location'])]

    def __str__(self):
        return f"{self.street_address}, {self.city}"

    def save(self, *args, **kwargs):
        """Optional geocode hook - currently not implemented"""
        if not self.location and self.street_address:
            # You can call a geocoding service here if you want
            pass
        super().save(*args, **kwargs)
