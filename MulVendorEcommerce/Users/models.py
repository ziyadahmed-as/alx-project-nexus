import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError(_('Users must have an email address'))
        if not username:
            raise ValueError(_('Users must have a username'))

        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMIN)
        extra_fields.setdefault('is_verified', True)

        if not extra_fields.get('is_staff'):
            raise ValueError(_('Superuser must have is_staff=True.'))
        if not extra_fields.get('is_superuser'):
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, username, password, **extra_fields)

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', _('Admin')
        CUSTOMER = 'CUSTOMER', _('Customer')
        VENDOR = 'VENDOR', _('Vendor')
        VENDOR_STAFF = 'VENDOR_STAFF', _('Vendor Staff')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, error_messages={
        'unique': _('A user with that email already exists.'),
    })
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_active = models.DateTimeField(null=True, blank=True)

    # Remove username from REQUIRED_FIELDS since we're using email as primary identifier
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Role.ADMIN
            self.is_verified = True
        super().save(*args, **kwargs)

class Customer(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        primary_key=True, 
        related_name='customer_profile'
    )
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(
        upload_to='customer_profiles/', 
        null=True, 
        blank=True
    )
    preferred_language = models.CharField(max_length=10, default='en')
    marketing_opt_in = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('customer')
        verbose_name_plural = _('customers')

    def __str__(self):
        return f"{self.full_name} ({self.user.email})"

    @property
    def full_name(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

class Vendor(models.Model):
    class VerificationStatus(models.TextChoices):
        PENDING = 'pending', _('Pending Verification')
        VERIFIED = 'verified', _('Verified')
        REJECTED = 'rejected', _('Rejected')
        SUSPENDED = 'suspended', _('Suspended')

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='vendor_profile'
    )
    business_name = models.CharField(max_length=100)
    business_email = models.EmailField()
    business_phone = models.CharField(max_length=20)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    business_registration = models.FileField(
        upload_to='vendor_documents/',
        null=True,
        blank=True
    )
    store_logo = models.ImageField(upload_to='vendor_logos/')
    store_banner = models.ImageField(upload_to='vendor_banners/', null=True, blank=True)
    store_description = models.TextField()
    shipping_policy = models.TextField()
    return_policy = models.TextField()
    average_rating = models.FloatField(default=0.0)
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING
    )
    verification_notes = models.TextField(blank=True, null=True)
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_vendors'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('vendor')
        verbose_name_plural = _('vendors')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.business_name} ({self.user.email})"

    def save(self, *args, **kwargs):
        if self.verification_status == self.VerificationStatus.VERIFIED and not self.verified_at:
            self.verified_at = timezone.now()
        super().save(*args, **kwargs)

class AdminProfile(models.Model):
    class AccessLevel(models.TextChoices):
        SUPER = 'SUPER', _('Super Admin')
        CONTENT = 'CONTENT', _('Content Manager')
        SUPPORT = 'SUPPORT', _('Support Staff')
        FINANCE = 'FINANCE', _('Finance Admin')

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='admin_profile'
    )
    access_level = models.CharField(
        max_length=20,
        choices=AccessLevel.choices,
        default=AccessLevel.SUPPORT
    )
    department = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True)
    can_manage_users = models.BooleanField(default=False)
    can_manage_vendors = models.BooleanField(default=False)
    can_manage_content = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('admin profile')
        verbose_name_plural = _('admin profiles')

    def __str__(self):
        return f"{self.get_access_level_display()} ({self.user.email})"

class VendorEmployee(models.Model):
    class Role(models.TextChoices):
        MANAGER = 'MANAGER', _('Manager')
        STAFF = 'STAFF', _('Staff')
        CUSTOMER_SERVICE = 'CS', _('Customer Service')
        WAREHOUSE = 'WAREHOUSE', _('Warehouse Staff')

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='vendor_employee_profile'
    )
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name='employees'
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    department = models.CharField(max_length=100, blank=True, null=True)
    hire_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('vendor employee')
        verbose_name_plural = _('vendor employees')
        ordering = ['vendor', 'role']

    def __str__(self):
        return f"{self.user.email} ({self.get_role_display()} at {self.vendor.business_name})"

class Address(models.Model):
    class Type(models.TextChoices):
        HOME = 'HOME', _('Home')
        WORK = 'WORK', _('Work')
        BILLING = 'BILLING', _('Billing')
        SHIPPING = 'SHIPPING', _('Shipping')
        OTHER = 'OTHER', _('Other')

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='addresses'
    )
    type = models.CharField(max_length=10, choices=Type.choices)
    recipient_name = models.CharField(max_length=100, blank=True, null=True)
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('address')
        verbose_name_plural = _('addresses')
        ordering = ['-is_default', 'user', 'type']
        unique_together = ('user', 'type', 'street', 'city', 'postal_code')

    def __str__(self):
        return f"{self.get_type_display()} address for {self.user.email}"

    def save(self, *args, **kwargs):
        if self.is_default:
            # Ensure only one default address per user
            self.__class__.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)