from django.db import models
from django.conf import settings

class VendorProfile(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    )
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='vendor_profile')
    
    # Vendor Personal Information
    vendor_name = models.CharField(max_length=255, blank=True, default='', help_text="Owner/Contact person name")
    
    # Business Information
    business_name = models.CharField(max_length=255)
    business_description = models.TextField()
    business_phone = models.CharField(max_length=20)
    business_email = models.EmailField()
    business_logo = models.ImageField(upload_to='vendor_logos/', null=True, blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    bank_account = models.CharField(max_length=100, blank=True)
    
    # Address Details
    address = models.TextField(blank=True, help_text="Physical office address")
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='Ethiopia')
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Map Coordinates
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Social Media
    facebook_url = models.URLField(max_length=255, blank=True)
    instagram_url = models.URLField(max_length=255, blank=True)
    twitter_url = models.URLField(max_length=255, blank=True)
    telegram_url = models.URLField(max_length=255, blank=True)
    website_url = models.URLField(max_length=255, blank=True)
    
    # Store Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_active = models.BooleanField(default=True, help_text="Account active status")
    
    # Verification Info (Store Level)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                    null=True, blank=True, related_name='verified_vendors')
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Suspension Info
    suspended_at = models.DateTimeField(null=True, blank=True, help_text="When account was suspended")
    suspended_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name='suspended_vendors')
    suspension_reason = models.TextField(blank=True, help_text="Reason for suspension")
    
    # Metrics
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_orders = models.IntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vendor_profiles'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['business_name']),
        ]
    
    def __str__(self):
        return self.business_name


class KYCVerification(models.Model):
    """Model for KYC verification process - Only for Vendors"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='kyc_verification', 
                                limit_choices_to={'role': 'vendor'})
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Personal Information
    full_name = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    nationality = models.CharField(max_length=100)
    address = models.TextField()
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    
    # Verification Details
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='kyc_reviews')
    admin_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    
    class Meta:
        db_table = 'kyc_verifications'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['submitted_at']),
        ]
    
    def __str__(self):
        return f"KYC for {self.user.username} - {self.status}"


class KYCDocument(models.Model):
    """Model for KYC document uploads"""
    DOCUMENT_TYPES = (
        ('identity', 'Identity Document'),
        ('passport', 'Passport'),
        ('drivers_license', 'Driver\'s License'),
        ('proof_of_address', 'Proof of Address'),
        ('business_license', 'Business License'),
        ('tax_certificate', 'Tax Certificate'),
        ('bank_statement', 'Bank Statement'),
        ('other', 'Other'),
    )
    
    kyc = models.ForeignKey(KYCVerification, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to='kyc_documents/%Y/%m/')
    original_filename = models.CharField(max_length=255)
    file_size = models.IntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'kyc_documents'
        indexes = [
            models.Index(fields=['kyc', 'document_type']),
            models.Index(fields=['uploaded_at']),
        ]
    
    def __str__(self):
        return f"{self.document_type} for {self.kyc.user.username}"
