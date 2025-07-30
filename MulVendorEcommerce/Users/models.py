import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser
 
class UserManager(BaseUserManager):
    """Custom user manager for handling user creation"""
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError(_('Users must have an email address'))
        if not username:
            raise ValueError(_('Users must have a username'))
        user = self.model(email=self.normalize_email(email),username=username,**extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    # this method is used to create a superuser with specific permissions
    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMIN)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))  
        return self.create_user(email, username, password, **extra_fields)
# User models 
import uuid
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', _('Admin')
        CUSTOMER = 'CUSTOMER', _('Customer')
        VENDOR = 'VENDOR', _('Vendor')

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('ID')
    )
    email = models.EmailField(
        unique=True,
        verbose_name=_('email address'),
        error_messages={
            'unique': _("A user with that email already exists."),
        }
    )
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name=_('phone number')
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name=_('verified status')
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
        verbose_name=_('role')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('last updated')
    )

    groups = models.ManyToManyField(
        Group,
        related_name='custom_user_set',
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        verbose_name=_('groups')
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='custom_user_set',
        blank=True,
        help_text=_('Specific permissions for this user.'),
        verbose_name=_('user permissions')
    )

    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

# This models used to Sore the Customer data 
class Customer(models.Model):
    """
    Extended profile for customers with personal information.
    One-to-one relationship with User model.
    """
    user = models.OneToOneField(User,on_delete=models.CASCADE,primary_key=True,related_name='customer')
    first_name = models.CharField( max_length=30, blank=True, null=True, verbose_name=_('first name') )
    last_name = models.CharField(max_length=30,blank=True,null=True,verbose_name=_('last name'))
    location_lat = models.FloatField( blank=True, null=True, verbose_name=_('latitude') )
    location_long = models.FloatField( blank=True, null=True, verbose_name=_('longitude') )
    device_id = models.CharField( max_length=100, blank=True, null=True, verbose_name=_('device ID' ))

    class Meta:
        verbose_name = _('customer')
        verbose_name_plural = _('customers')

    def __str__(self):
        return f"{self.full_name} ({self.user.email})"

    @property
    def full_name(self):
        """Return the customer's full name."""
        return f"{self.first_name} {self.last_name}".strip()

# This model is used to manage vendor profiles with business information.
class Vendor(models.Model):
    """
    Extended profile for vendors with business information.
    One-to-one relationship with User model.
    """
    user = models.OneToOneField( User, on_delete=models.CASCADE, primary_key=True, related_name='vendor' )
    store_name = models.CharField( max_length=100, verbose_name=_('store name') )
    store_logo = models.ImageField( upload_to='vendor_logos/', verbose_name=_('store logo') )
    store_description = models.TextField(verbose_name=_('store description'))
    shipping_policy = models.TextField( verbose_name=_('shipping policy') )
    return_policy = models.TextField( verbose_name=_('return policy') )
    is_approved = models.BooleanField( default=False,  verbose_name=_('approved status') )
    store_rating = models.FloatField( default=0.0,verbose_name=_('store rating'))

    class Meta:
        verbose_name = _('vendor')
        verbose_name_plural = _('vendors')
        ordering = ['-is_approved', 'store_name']
    def __str__(self):
        return f"{self.store_name} ({self.user.email})"
# this model is used to manage admin users with specific access levels and permissions.
class AdminProfile(models.Model):
    """
    Extended profile for admin users with additional access control.
    One-to-one relationship with User model.
    """
    class AccessLevel(models.TextChoices):
        SUPER = 'SUPER', _('Super Admin')
        MOD = 'MOD', _('Moderator')
        SUPPORT = 'SUPPORT', _('Support Staff')

    user = models.OneToOneField(User,on_delete=models.CASCADE,primary_key=True,related_name='admin_profile')
    access_level = models.CharField( max_length=20, choices=AccessLevel.choices, default=AccessLevel.SUPPORT, verbose_name=_('access level') )
    notes = models.TextField( blank=True, verbose_name=_('admin notes') )

    class Meta:
        verbose_name = _('admin profile')
        verbose_name_plural = _('admin profiles')

    def __str__(self):
        return f"{self.get_access_level_display()} ({self.user.email})"
# This model is used to manage vendor employees with specific roles and permissions.
class VendorEmployee(models.Model):
    """
    Model representing employees working for vendors with specific permissions.
    """
    class EmployeeRole(models.TextChoices):
        MANAGER = 'MANAGER', _('Manager')
        STAFF = 'STAFF', _('Staff')
        CUSTOMER_SERVICE = 'CS', _('Customer Service')

    id = models.UUIDField( primary_key=True, default=uuid.uuid4, editable=False, verbose_name=_('ID')) 
    user = models.ForeignKey( User, on_delete=models.CASCADE, related_name='vendor_employees', verbose_name=_('user')) 
    vendor = models.ForeignKey( Vendor, on_delete=models.CASCADE, related_name='employees', verbose_name=_('vendor') )
    role = models.CharField( max_length=20, choices=EmployeeRole.choices, verbose_name=_('employee role') )
    permissions = models.JSONField( default=dict, verbose_name=_('permissions') )
    is_active = models.BooleanField( default=True, verbose_name=_('active status') )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('created at')
    )
    updated_at = models.DateTimeField( auto_now=True, verbose_name=_('updated at') )

    class Meta:
        verbose_name = _('vendor employee')
        verbose_name_plural = _('vendor employees')
        unique_together = ('user', 'vendor')
        ordering = ['vendor', '-is_active', 'role']
    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()} at {self.vendor.store_name})"

class Address(models.Model):
    """
    Model for storing user addresses with geolocation data.
    """
    class AddressLabel(models.TextChoices):
        HOME = 'HOME', _('Home')
        WORK = 'WORK', _('Work')
        OTHER = 'OTHER', _('Other')

    id = models.UUIDField( primary_key=True, default=uuid.uuid4, editable=False, verbose_name=_('ID')) 
    user = models.ForeignKey( User, on_delete=models.CASCADE, related_name='addresses', verbose_name=_('user') )
    label = models.CharField( max_length=10, choices=AddressLabel.choices, verbose_name=_('address label') )
    street = models.CharField( max_length=255, verbose_name=_('street address') )
    city = models.CharField( max_length=100, verbose_name=_('city') )
    region = models.CharField( max_length=100, verbose_name=_('region/state') )
    country = models.CharField( max_length=100, verbose_name=_('country') ) 
    postal_code = models.CharField( max_length=20, verbose_name=_('postal code') )
    latitude = models.FloatField( null=True, blank=True, verbose_name=_('latitude') )
    longitude = models.FloatField( null=True, blank=True, verbose_name=_('longitude' ))
    phone_number = models.CharField( max_length=20, verbose_name=_('contact phone') )
    is_default = models.BooleanField( default=False, verbose_name=_('default address') )
    created_at = models.DateTimeField( auto_now_add=True, verbose_name=_('created at') )
    updated_at = models.DateTimeField( auto_now=True, verbose_name=_('updated at') )

    class Meta:
        verbose_name = _('address')
        verbose_name_plural = _('addresses')
        ordering = ['-is_default', 'user', 'label']

    def __str__(self):
        return f"{self.get_label_display()} address for {self.user.username}"
    def save(self, *args, **kwargs):
        # Ensure only one default address per user
        if self.is_default:
            self.__class__.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
        