from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth import get_user_model, authenticate
from .models import (
    User, CustomerProfile, Vendor, AdminProfile, VendorEmployee, Address
)
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration with password validation"""
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        min_length=8,
        error_messages={
            'min_length': _('Password must be at least 8 characters long.')
        }
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    role = serializers.ChoiceField(
        choices=User.Role.choices,
        default=User.Role.CUSTOMER
    )

    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'phone_number',
            'password', 'password_confirm', 'role'
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': _("Passwords do not match")
            })
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone_number=validated_data.get('phone_number'),
            role=validated_data.get('role', User.Role.CUSTOMER)
        )
        return user

class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login with email/password"""
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                email=email,
                password=password
            )
            if not user:
                raise serializers.ValidationError(
                    _("Unable to log in with provided credentials"),
                    code='authorization'
                )
        else:
            raise serializers.ValidationError(
                _("Must include 'email' and 'password'"),
                code='authorization'
            )

        data['user'] = user
        return data

class UserSerializer(serializers.ModelSerializer):
    """Complete user serializer for general user data"""
    email = serializers.EmailField(read_only=True)
    role = serializers.ChoiceField(choices=User.Role.choices, read_only=True)
    full_name = serializers.SerializerMethodField()
    last_active = serializers.DateTimeField(read_only=True)
    is_verified = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone_number', 'role', 'is_active', 'is_verified',
            'last_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_full_name(self, obj):
        return obj.full_name

class CustomerProfileSerializer(serializers.ModelSerializer):
    """Customer profile serializer"""
    user = UserSerializer(read_only=True)
    age = serializers.SerializerMethodField()

    class Meta:
        model = CustomerProfile
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_age(self, obj):
        if not obj.date_of_birth:
            return None
        today = timezone.now().date()
        return today.year - obj.date_of_birth.year - (
            (today.month, today.day) < (obj.date_of_birth.month, obj.date_of_birth.day)
        )

class VendorProfileSerializer(serializers.ModelSerializer):
    """Vendor profile serializer"""
    user = UserSerializer(read_only=True)

    class Meta:
        model = Vendor
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'verification_status']

class AdminProfileSerializer(serializers.ModelSerializer):
    """Admin profile serializer"""
    user = UserSerializer(read_only=True)

    class Meta:
        model = AdminProfile
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class VendorEmployeeSerializer(serializers.ModelSerializer):
    """Vendor employee serializer"""
    user = UserSerializer(read_only=True)

    class Meta:
        model = VendorEmployee
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class AddressSerializer(serializers.ModelSerializer):
    """Address serializer"""
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Address
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class PasswordResetSerializer(serializers.Serializer):
    """Password reset request serializer"""
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    """Password reset confirmation serializer"""
    new_password = serializers.CharField(
        style={'input_type': 'password'},
        min_length=8
    )
    new_password_confirm = serializers.CharField(
        style={'input_type': 'password'}
    )

    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': _("Passwords do not match")
            })
        return data