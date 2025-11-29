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
    business_name = models.CharField(max_length=255)
    business_description = models.TextField()
    business_address = models.TextField()
    business_phone = models.CharField(max_length=20)
    business_email = models.EmailField()
    business_logo = models.ImageField(upload_to='vendor_logos/', null=True, blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    bank_account = models.CharField(max_length=100, blank=True)
    
    # Office/Physical Address Details
    office_address = models.TextField(blank=True, help_text="Physical office address")
    office_city = models.CharField(max_length=100, blank=True)
    office_state = models.CharField(max_length=100, blank=True)
    office_country = models.CharField(max_length=100, default='Ethiopia')
    office_postal_code = models.CharField(max_length=20, blank=True)
    
    # Social Media Links
    facebook_url = models.URLField(max_length=255, blank=True, help_text="Facebook page URL")
    instagram_url = models.URLField(max_length=255, blank=True, help_text="Instagram profile URL")
    twitter_url = models.URLField(max_length=255, blank=True, help_text="X.com (Twitter) profile URL")
    telegram_url = models.URLField(max_length=255, blank=True, help_text="Telegram channel/group URL")
    website_url = models.URLField(max_length=255, blank=True, help_text="Business website URL")
    
    # Verification Documents
    business_license = models.FileField(upload_to='vendor_documents/licenses/', null=True, blank=True, 
                                       help_text="Business license or registration certificate")
    tax_certificate = models.FileField(upload_to='vendor_documents/tax/', null=True, blank=True,
                                       help_text="Tax registration certificate")
    id_document = models.FileField(upload_to='vendor_documents/ids/', null=True, blank=True,
                                   help_text="Owner's ID or passport")
    bank_statement = models.FileField(upload_to='vendor_documents/bank/', null=True, blank=True,
                                     help_text="Recent bank statement")
    additional_document = models.FileField(upload_to='vendor_documents/additional/', null=True, blank=True,
                                          help_text="Any additional supporting document")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    verification_notes = models.TextField(blank=True)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                    null=True, blank=True, related_name='verified_vendors')
    verified_at = models.DateTimeField(null=True, blank=True)
    
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
