import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.core.cache import cache
from django.db.models import Index, UniqueConstraint, Q
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone


class UserManager(BaseUserManager):
    """Advanced User Manager with caching and query optimization"""
    
    def _create_user(self, email, password=None, **extra_fields):
        """Create user with comprehensive validation and cache management"""
        if not email:
            raise ValueError(_('The Email field must be set'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        
        # Clear relevant caches
        cache.delete_pattern(f'user_{user.id}_*')
        cache.delete('all_active_users')
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMIN)
        extra_fields.setdefault('is_verified', True)
        return self._create_user(email, password, **extra_fields)

    def get_by_id_cached(self, user_id):
        """Retrieve user with cache support and fallback"""
        cache_key = f'user_{user_id}_full'
        user_data = cache.get(cache_key)
        
        if not user_data:
            try:
                user = self.select_related(
                    'customer_profile',
                    'vendor',
                    'admin_profile',
                    'vendor_employee'
                ).get(pk=user_id)
                user_data = {
                    'user': user,
                    'profile': self._get_user_profile_data(user)
                }
                cache.set(cache_key, user_data, 3600)
            except User.DoesNotExist:
                return None
        return user_data

    def _get_user_profile_data(self, user):
        """Helper method to get profile data based on role"""
        if hasattr(user, 'customer_profile'):
            return {'customer': user.customer_profile}
        elif hasattr(user, 'vendor'):
            return {'vendor': user.vendor}
        elif hasattr(user, 'admin_profile'):
            return {'admin': user.admin_profile}
        elif hasattr(user, 'vendor_employee'):
            return {'vendor_employee': user.vendor_employee}
        return None


class User(AbstractUser):
    """Enhanced User model with role-based access and caching"""
    
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', _('Admin')
        CUSTOMER = 'CUSTOMER', _('Customer')
        VENDOR = 'VENDOR', _('Vendor')
        VENDOR_STAFF = 'VENDOR_STAFF', _('Vendor Staff')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text=_('Optional username, defaults to email if not provided')
    )
    email = models.EmailField(
        unique=True,
        db_index=True,
        error_messages={
            'unique': _('A user with that email already exists.')
        }
    )
    phone_number = models.CharField(
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message=_("Phone number must be in format: '+999999999'. Up to 15 digits.")
        )],
        max_length=17,
        blank=True,
        null=True,
        db_index=True
    )
    is_verified = models.BooleanField(
        default=False,
        help_text=_('Designates whether the user has verified their email.')
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
        db_index=True
    )
    last_active = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Last time the user was active on the platform')
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            Index(fields=['email'], name='user_email_idx'),
            Index(fields=['role', 'is_verified'], name='user_role_verified_idx'),
            Index(fields=['last_active'], name='user_last_active_idx'),
        ]
        constraints = [
            UniqueConstraint(fields=['email'], name='unique_user_email')
        ]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        """Return the full name of the user"""
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        """Override save with cache invalidation and role enforcement"""
        if self.is_superuser:
            self.role = self.Role.ADMIN
            self.is_verified = True
        
        if not self.username:
            self.username = self.email
            
        super().save(*args, **kwargs)
        self._update_caches()

    def delete(self, *args, **kwargs):
        """Override delete with comprehensive cache invalidation"""
        cache.delete_pattern(f'user_{self.id}_*')
        cache.delete('all_active_users')
        super().delete(*args, **kwargs)

    def _update_caches(self):
        """Update all related caches for this user"""
        cache.set(f'user_{self.id}_basic', self, 3600)
        if hasattr(self, 'customer_profile'):
            cache.set(f'user_{self.id}_customer', self.customer_profile, 3600)
        if hasattr(self, 'vendor'):
            cache.set(f'user_{self.id}_vendor', self.vendor, 3600)
        if hasattr(self, 'admin_profile'):
            cache.set(f'user_{self.id}_admin', self.admin_profile, 3600)
        if hasattr(self, 'vendor_employee'):
            cache.set(f'user_{self.id}_employee', self.vendor_employee, 3600)


class CustomerProfile(models.Model):
    """Customer Profile model with enhanced features"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='customer_profile'
    )
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        help_text=_("Customer's date of birth")
    )
    profile_picture = models.ImageField(
        upload_to='customer_profiles/',
        null=True,
        blank=True,
        help_text=_("Profile picture for the customer")
    )
    preferred_language = models.CharField(
        max_length=10,
        default='en',
        choices=[
            ('en', 'English'),
            ('fr', 'French'),
            ('es', 'Spanish')
        ],
        help_text=_("Preferred language for communication")
    )
    newsletter_subscription = models.BooleanField(
        default=False,
        db_index=True,
        help_text=_("Whether the customer subscribes to newsletters")
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = _('Customer Profile')
        verbose_name_plural = _('Customer Profiles')
        ordering = ['-created_at']
        indexes = [
            Index(fields=['user'], name='customer_user_idx'),
            Index(fields=['newsletter_subscription'], name='customer_newsletter_idx'),
        ]

    def __str__(self):
        return f"{self.user.email} (Customer)"

    @property
    def age(self):
        """Calculate age from date of birth"""
        if not self.date_of_birth:
            return None
            
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < 
            (self.date_of_birth.month, self.date_of_birth.day)
        )

    def save(self, *args, **kwargs):
        """Override save with cache invalidation"""
        super().save(*args, **kwargs)
        cache.delete(f'user_{self.user_id}_customer')
        cache.delete(f'user_{self.user_id}_full')


class Vendor(models.Model):
    """Vendor model with business verification and indexing"""
    
    class BusinessType(models.TextChoices):
        RETAIL = 'RETAIL', _('Retail')
        WHOLESALE = 'WHOLESALE', _('Wholesale')
        SERVICE = 'SERVICE', _('Service')
        MANUFACTURING = 'MANUFACTURING', _('Manufacturing')
        OTHER = 'OTHER', _('Other')

    class VerificationStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        VERIFIED = 'VERIFIED', _('Verified')
        REJECTED = 'REJECTED', _('Rejected')
        SUSPENDED = 'SUSPENDED', _('Suspended')

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='vendor'
    )
    company_registration_number = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text=_("Official company registration number")
    )
    business_type = models.CharField(
        max_length=50,
        choices=BusinessType.choices,
        default=BusinessType.RETAIL,
        db_index=True
    )
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
        db_index=True
    )
    tax_identification_number = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text=_("Tax ID number for the business")
    )
    business_email = models.EmailField(
        unique=True,
        db_index=True,
        help_text=_("Official business email address")
    )
    business_phone = models.CharField(
        max_length=20,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$')],
        help_text=_("Official business phone number")
    )
    years_in_business = models.PositiveIntegerField(
        default=0,
        help_text=_("Number of years the business has been operating")
    )
    accepted_terms = models.BooleanField(
        default=False,
        help_text=_("Whether the vendor accepted terms and conditions")
    )
    terms_accepted_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Date when terms were accepted")
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = _('Vendor')
        verbose_name_plural = _('Vendors')
        ordering = ['-created_at']
        indexes = [
            Index(fields=['business_type', 'verification_status'], name='vendor_type_status_idx'),
            Index(fields=['company_registration_number'], name='vendor_reg_num_idx'),
            Index(fields=['business_email'], name='vendor_business_email_idx'),
        ]
        constraints = [
            UniqueConstraint(fields=['tax_identification_number'], name='unique_vendor_tax_id'),
            UniqueConstraint(fields=['business_email'], name='unique_vendor_business_email')
        ]

    def __str__(self):
        return f"{self.user.email} (Vendor)"

    def save(self, *args, **kwargs):
        """Override save with cache invalidation"""
        super().save(*args, **kwargs)
        cache.delete(f'user_{self.user_id}_vendor')
        cache.delete(f'user_{self.user_id}_full')


class AdminProfile(models.Model):
    """Administrator profile with department and access control"""
    
    class Department(models.TextChoices):
        IT = 'IT', _('Information Technology')
        FINANCE = 'FINANCE', _('Finance')
        OPERATIONS = 'OPERATIONS', _('Operations')
        MARKETING = 'MARKETING', _('Marketing')
        SALES = 'SALES', _('Sales')
        SUPPORT = 'SUPPORT', _('Customer Support')

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='admin_profile'
    )
    department = models.CharField(
        max_length=20,
        choices=Department.choices,
        db_index=True
    )
    position = models.CharField(
        max_length=100,
        help_text=_("Job title or position in the organization")
    )
    access_level = models.PositiveIntegerField(
        default=1,
        db_index=True,
        help_text=_("Numerical representation of access privileges")
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text=_("Additional notes about the admin")
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = _('Admin Profile')
        verbose_name_plural = _('Admin Profiles')
        ordering = ['department', '-access_level']
        indexes = [
            Index(fields=['department', 'access_level'], name='admin_dept_access_idx'),
        ]

    def __str__(self):
        return f"{self.user.email} (Admin)"

    def save(self, *args, **kwargs):
        """Override save with cache invalidation"""
        super().save(*args, **kwargs)
        cache.delete(f'user_{self.user_id}_admin')
        cache.delete(f'user_{self.user_id}_full')
        cache.delete(f'admins_{self.department}')


class VendorEmployee(models.Model):
    """Vendor staff/employee model with role management"""
    
    class EmployeeRole(models.TextChoices):
        MANAGER = 'MANAGER', _('Manager')
        STAFF = 'STAFF', _('Staff')
        DELIVERY = 'DELIVERY', _('Delivery')
        CUSTOMER_SERVICE = 'CUSTOMER_SERVICE', _('Customer Service')

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='vendor_employee'
    )
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name='employees',
        db_index=True
    )
    employee_id = models.CharField(
        max_length=50,
        unique=True,
        help_text=_("Internal employee ID")
    )
    role = models.CharField(
        max_length=20,
        choices=EmployeeRole.choices,
        default=EmployeeRole.STAFF,
        db_index=True
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Department within the vendor organization")
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text=_("Whether the employee is currently active")
    )
    hire_date = models.DateField(
        db_index=True,
        help_text=_("Date when employee was hired")
    )
    termination_date = models.DateField(
        null=True,
        blank=True,
        help_text=_("Date when employment was terminated")
    )
    permissions = models.JSONField(
        default=dict,
        help_text=_("JSON structure defining employee permissions")
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = _('Vendor Employee')
        verbose_name_plural = _('Vendor Employees')
        ordering = ['vendor', '-hire_date']
        indexes = [
            Index(fields=['vendor', 'is_active'], name='vendor_employee_active_idx'),
            Index(fields=['role', 'is_active'], name='employee_role_active_idx'),
        ]
        constraints = [
            UniqueConstraint(fields=['employee_id'], name='unique_employee_id')
        ]

    def __str__(self):
        return f"{self.user.email} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        """Override save with cache invalidation"""
        super().save(*args, **kwargs)
        cache.delete(f'user_{self.user_id}_employee')
        cache.delete(f'user_{self.user_id}_full')
        cache.delete(f'vendor_{self.vendor_id}_employees')


class Address(models.Model):
    """Comprehensive address model with geocoding support"""
    
    class AddressType(models.TextChoices):
        BILLING = 'BILLING', _('Billing')
        SHIPPING = 'SHIPPING', _('Shipping')
        BUSINESS = 'BUSINESS', _('Business')
        OTHER = 'OTHER', _('Other')

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='addresses',
        db_index=True
    )
    address_type = models.CharField(
        max_length=20,
        choices=AddressType.choices,
        default=AddressType.SHIPPING,
        db_index=True
    )
    recipient_name = models.CharField(
        max_length=100,
        null=True, 
        blank=True,
        help_text=_("Name of the person receiving shipments")
    )
    company_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Company name for business addresses")
    )
    street_address = models.CharField(
        max_length=255, 
        null=True, 
        blank=True,
        validators=[RegexValidator(regex=r'^[A-Za-z0-9\s,.-]+$')],
        help_text=_("Primary street address line")
    )
    apartment_address = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Apartment, suite, or building number")
    )
    city = models.CharField(
        max_length=100,
        help_text=_("City or locality name")
    )
    state = models.CharField(
        max_length=100,
        null=True, 
        blank=True,
        validators=[RegexValidator(regex=r'^[A-Za-z\s]+$')],
        help_text=_("State, province, or region")
    )
    postal_code = models.CharField(
        max_length=20,
        db_index=True,
        help_text=_("ZIP or postal code")
    )
    country = models.CharField(
        max_length=100,
        default='Ethiopia',
        help_text=_("Country name")
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$')],
        help_text=_("Contact phone number for delivery")
    )
    is_default = models.BooleanField(
        default=False,
        db_index=True,
        help_text=_("Set as default address for this type")
    )
    location_coordinates = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Latitude,Longitude for mapping")
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = _('Address')
        verbose_name_plural = _('Addresses')
        ordering = ['-is_default', '-created_at']
        indexes = [
            Index(fields=['user', 'is_default'], name='user_default_address_idx'),
            Index(fields=['postal_code'], name='address_postal_code_idx'),
            Index(fields=['address_type'], name='address_type_idx'),
        ]
        constraints = [
            UniqueConstraint(
                fields=['user', 'address_type'],
                condition=Q(is_default=True),
                name='unique_default_address_per_type'
            )
        ]

    def __str__(self):
        return f"{self.recipient_name}, {self.city}, {self.country}"

    def get_google_maps_url(self):
        """Generate Google Maps URL from address components"""
        if not all([self.street_address, self.city, self.state, self.country]):
            return None
        base = "https://www.google.com/maps/search/?api=1&query="
        query = f"{self.street_address},{self.city},{self.state},{self.country}"
        return base + query.replace(' ', '+')

    def save(self, *args, **kwargs):
        """Handle default address logic and cache invalidation"""
        if self.is_default:
            # Clear existing default for this address type
            Address.objects.filter(
                user=self.user,
                address_type=self.address_type,
                is_default=True
            ).exclude(pk=self.pk if self.pk else None).update(is_default=False)
            
        super().save(*args, **kwargs)
        cache.delete(f'user_{self.user_id}_addresses')
        if self.is_default:
            cache.delete(f'user_{self.user_id}_full')


# Signal handlers for cache management
@receiver(post_save, sender=User)
def user_post_save(sender, instance, **kwargs):
    """Update caches after user save"""
    instance._update_caches()

@receiver(post_delete, sender=VendorEmployee)
def vendor_employee_post_delete(sender, instance, **kwargs):
    """Clear cache when employee is deleted"""
    cache.delete(f'vendor_{instance.vendor_id}_employees')
    cache.delete(f'user_{instance.user_id}_employee')
    cache.delete(f'user_{instance.user_id}_full')

@receiver([post_save, post_delete], sender=Address)
def address_cache_invalidation(sender, instance, **kwargs):
    """Clear address cache on changes"""
    cache.delete(f'user_{instance.user_id}_addresses')
    if instance.is_default:
        cache.delete(f'user_{instance.user_id}_full')