from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid

class User(AbstractUser):
    ROLE_CHOICES = (
        ('super_admin', 'Super Admin'),
        ('admin', 'Admin'),
        ('vendor', 'Vendor'),
        ('buyer', 'Buyer'),
    )
    
    KYC_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    # Basic Information
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='buyer')
    phone = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Verification Status
    is_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    kyc_status = models.CharField(max_length=20, choices=KYC_STATUS_CHOICES, default='pending')
    
    # Security Features
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=32, blank=True)
    backup_codes = models.JSONField(default=list, blank=True)
    
    # Login Security
    failed_login_attempts = models.IntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_password_change = models.DateTimeField(default=timezone.now)
    
    # Verification Tokens
    email_verification_token = models.UUIDField(null=True, blank=True, unique=True)
    phone_verification_code = models.CharField(max_length=6, blank=True)
    phone_verification_expires = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['kyc_status']),
            models.Index(fields=['email_verification_token']),
        ]
    
    def __str__(self):
        return f"{self.username} ({self.role})"
    
    def is_account_locked(self):
        """Check if account is currently locked"""
        if self.account_locked_until:
            return timezone.now() < self.account_locked_until
        return False
    
    def lock_account(self, duration_minutes=30):
        """Lock account for specified duration"""
        self.account_locked_until = timezone.now() + timezone.timedelta(minutes=duration_minutes)
        self.save(update_fields=['account_locked_until'])
    
    def unlock_account(self):
        """Unlock account and reset failed attempts"""
        self.account_locked_until = None
        self.failed_login_attempts = 0
        self.save(update_fields=['account_locked_until', 'failed_login_attempts'])
    
    def increment_failed_login(self):
        """Increment failed login attempts and lock if threshold reached"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:  # Lock after 5 failed attempts
            self.lock_account()
        self.save(update_fields=['failed_login_attempts'])
    
    def reset_failed_login(self):
        """Reset failed login attempts on successful login"""
        self.failed_login_attempts = 0
        self.save(update_fields=['failed_login_attempts'])
    
    def is_super_admin(self):
        """Check if user is a super admin"""
        return self.role == 'super_admin'
    
    def is_admin(self):
        """Check if user is an admin (includes super admin)"""
        return self.role in ['admin', 'super_admin']
    
    def is_vendor(self):
        """Check if user is a vendor"""
        return self.role == 'vendor'
    
    def is_buyer(self):
        """Check if user is a buyer"""
        return self.role == 'buyer'
    
    def can_create_admin(self):
        """Check if user can create admin accounts"""
        return self.is_super_admin()
    
    def can_verify_kyc(self):
        """Check if user can verify KYC documents"""
        return self.is_admin()  # Both admin and super_admin can verify KYC


class PasswordResetToken(models.Model):
    """Model to track password reset tokens"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'password_reset_tokens'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'used']),
        ]
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        return not self.used and not self.is_expired()


class LoginAttempt(models.Model):
    """Model to track login attempts for security monitoring"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    success = models.BooleanField()
    failure_reason = models.CharField(max_length=100, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'login_attempts'
        indexes = [
            models.Index(fields=['email', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['success', 'timestamp']),
        ]



