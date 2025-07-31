# users/models.py

import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission
from django.db import models
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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, error_messages={
        'unique': _('A user with that email already exists.'),
    })
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    updated_at = models.DateTimeField(auto_now=True)

    groups = models.ManyToManyField(Group, related_name='custom_user_set', blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name='custom_user_set', blank=True)

    REQUIRED_FIELDS = ['email']

    objects = UserManager()

    def __str__(self):
        return self.username


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='customer')
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    location_lat = models.FloatField(blank=True, null=True)
    location_long = models.FloatField(blank=True, null=True)
    device_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.full_name} ({self.user.email})"

    @property
    def full_name(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip()


class Vendor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='vendor')
    store_name = models.CharField(max_length=100)
    store_logo = models.ImageField(upload_to='vendor_logos/')
    store_description = models.TextField()
    shipping_policy = models.TextField()
    return_policy = models.TextField()
    is_approved = models.BooleanField(default=False)
    store_rating = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.store_name} ({self.user.email})"


class AdminProfile(models.Model):
    class AccessLevel(models.TextChoices):
        SUPER = 'SUPER', _('Super Admin')
        MOD = 'MOD', _('Moderator')
        SUPPORT = 'SUPPORT', _('Support Staff')

    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='admin_profile')
    access_level = models.CharField(max_length=20, choices=AccessLevel.choices, default=AccessLevel.SUPPORT)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.get_access_level_display()} ({self.user.email})"


class VendorEmployee(models.Model):
    class EmployeeRole(models.TextChoices):
        MANAGER = 'MANAGER', _('Manager')
        STAFF = 'STAFF', _('Staff')
        CUSTOMER_SERVICE = 'CS', _('Customer Service')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vendor_employees')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='employees')
    role = models.CharField(max_length=20, choices=EmployeeRole.choices)
    permissions = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'vendor')

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()} at {self.vendor.store_name})"


class Address(models.Model):
    class AddressLabel(models.TextChoices):
        HOME = 'HOME', _('Home')
        WORK = 'WORK', _('Work')
        OTHER = 'OTHER', _('Other')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    label = models.CharField(max_length=10, choices=AddressLabel.choices)
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    phone_number = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', 'user', 'label']

    def __str__(self):
        return f"{self.get_label_display()} address for {self.user.username}"

    def save(self, *args, **kwargs):
        if self.is_default:
            self.__class__.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
