from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.validators import RegexValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import PasswordResetToken, LoginAttempt
from django.db import models
import re

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name',
                  'role', 'phone', 'avatar', 'date_of_birth', 'is_verified', 
                  'email_verified', 'phone_verified', 'kyc_status', 
                  'two_factor_enabled', 'created_at', 'last_login']
        read_only_fields = ['id', 'is_verified', 'email_verified', 'phone_verified', 
                           'kyc_status', 'created_at', 'last_login']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    phone = serializers.CharField(
        required=False,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )]
    )
    terms_accepted = serializers.BooleanField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 
                  'first_name', 'last_name', 'role', 'phone', 'date_of_birth', 'terms_accepted']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Restrict role choices for public registration - no admin or super_admin
        self.fields['role'].choices = [
            ('buyer', 'Buyer'),
            ('vendor', 'Vendor'),
        ]
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_username(self, value):
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError("Username can only contain letters, numbers, and underscores.")
        return value
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords don't match"})
        
        if not data.get('terms_accepted'):
            raise serializers.ValidationError({"terms_accepted": "You must accept the terms and conditions"})
        
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        validated_data.pop('terms_accepted')
        # Auto-verify email for testing since we don't have email service yet
        validated_data['email_verified'] = True
        user = User.objects.create_user(**validated_data)
        
        # Send email verification (implement email service)
        # send_verification_email(user)
        
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # Get IP address and user agent for logging
        request = self.context.get('request')
        ip_address = self.get_client_ip(request) if request else None
        user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''
        
        login_input = attrs.get('username')  # DRF uses 'username' field for email/username
        
        try:
            # Check if user exists by email or username
            user = User.objects.filter(models.Q(email=login_input) | models.Q(username=login_input)).first()
            
            if not user:
                 raise User.DoesNotExist

            email = user.email # Ensure we have the email for logging
            
            # Check if account is locked
            if user.is_account_locked():
                LoginAttempt.objects.create(
                    user=user,
                    email=email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False,
                    failure_reason='Account locked'
                )
                raise serializers.ValidationError("Account is temporarily locked due to multiple failed login attempts.")
            
            # Authenticate user
            user_auth = authenticate(username=user.username, password=attrs.get('password'))
            if not user_auth:
                # Increment failed attempts
                user.increment_failed_login()
                
                LoginAttempt.objects.create(
                    user=user,
                    email=email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False,
                    failure_reason='Invalid credentials'
                )
                raise serializers.ValidationError("Invalid credentials.")
            
            # Check if email is verified
            if not user.email_verified:
                LoginAttempt.objects.create(
                    user=user,
                    email=email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False,
                    failure_reason='Email not verified'
                )
                raise serializers.ValidationError("Please verify your email address before logging in.")
            
            # Successful login
            user.reset_failed_login()
            user.last_login_ip = ip_address
            user.save(update_fields=['last_login_ip'])
            
            LoginAttempt.objects.create(
                user=user,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=True
            )
            
            # Generate tokens
            # Update username in attrs to match the actual username (not email) so super().validate works
            attrs['username'] = user.username
            data = super().validate(attrs)
            data['user'] = UserSerializer(user).data
            data['requires_2fa'] = user.two_factor_enabled
            
            return data
            
        except User.DoesNotExist:
            LoginAttempt.objects.create(
                email=login_input, # Log the input attempting to login
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                failure_reason='User not found'
            )
            raise serializers.ValidationError("Invalid credentials.")
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            # Don't reveal if email exists or not for security
            pass
        return value

class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    new_password = serializers.CharField(min_length=8, validators=[validate_password])
    new_password_confirm = serializers.CharField()
    
    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "Passwords don't match"})
        
        # Validate token
        try:
            reset_token = PasswordResetToken.objects.get(token=data['token'])
            if not reset_token.is_valid():
                raise serializers.ValidationError({"token": "Invalid or expired token"})
            data['reset_token'] = reset_token
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError({"token": "Invalid token"})
        
        return data

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8, validators=[validate_password])
    new_password_confirm = serializers.CharField()
    
    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect")
        return value
    
    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "Passwords don't match"})
        return data

class ProfileUpdateSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(
        required=False,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )]
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'date_of_birth']
    
    def validate_phone(self, value):
        user = self.context['request'].user
        if value and User.objects.filter(phone=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        return value



class AdminUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, required=False)
    send_email = serializers.BooleanField(default=False, write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 
                  'role', 'phone', 'is_active', 'is_verified', 'email_verified', 'send_email']
    
    def create(self, validated_data):
        send_email = validated_data.pop('send_email', False)
        password = validated_data.pop('password', None)
        
        if password:
            user = User.objects.create_user(**validated_data, password=password)
        else:
            import secrets
            random_password = secrets.token_urlsafe(12)
            user = User.objects.create_user(**validated_data, password=random_password)
        
        return user

class PasswordResetSerializer(serializers.Serializer):
    """Serializer for admin to reset user password"""
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return data
