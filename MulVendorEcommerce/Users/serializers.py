from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils import timezone
from .models import Customer, Vendor, AdminProfile, VendorEmployee, Address

User = get_user_model()

# ==================== AUTHENTICATION SERIALIZERS ====================

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer that includes additional user claims
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims to the token
        token['email'] = user.email
        token['role'] = user.role
        token['is_verified'] = user.is_verified
        token['is_staff'] = user.is_staff
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Include complete user data in the response
        data['user'] = UserSerializer(self.user).data
        return data

# ==================== CORE USER SERIALIZERS ====================

class UserSerializer(serializers.ModelSerializer):
    """
    Base serializer for user data (safe for general use)
    """
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'phone_number', 'role',
            'is_verified', 'date_joined', 'last_login'
        ]
        read_only_fields = fields

class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with password validation
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirmation = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password_confirmation', 'phone_number']
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True}
        }

    def validate(self, data):
        if data['password'] != data['password_confirmation']:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirmation')
        user = User.objects.create_user(**validated_data)
        return user

# ==================== PROFILE SERIALIZERS ====================
class UserDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for user information
    """
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'phone_number', 'role',
            'is_verified', 'is_active', 'is_staff', 'is_superuser',
            'date_joined', 'last_login', 'last_active'
        ]
        read_only_fields = fields
class CustomerProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for customer profile data including user information
    """
    user = UserSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = [
            'user', 'first_name', 'last_name', 'full_name', 'age',
            'date_of_birth', 'profile_picture', 'preferred_language',
            'marketing_opt_in', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_full_name(self, obj):
        return obj.full_name

    def get_age(self, obj):
        if obj.date_of_birth:
            today = timezone.now().date()
            return today.year - obj.date_of_birth.year - (
                (today.month, today.day) < (obj.date_of_birth.month, obj.date_of_birth.day)
            )
        return None

class VendorProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for vendor profile data with verification status
    """
    user = UserSerializer(read_only=True)
    verification_status = serializers.CharField(read_only=True)
    verification_details = serializers.SerializerMethodField()

    class Meta:
        model = Vendor
        fields = [
            'user', 'business_name', 'business_email', 'business_phone',
            'tax_id', 'store_logo', 'store_banner', 'store_description',
            'shipping_policy', 'return_policy', 'average_rating',
            'verification_status', 'verification_notes', 'verification_details',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'average_rating', 'verification_status', 'created_at', 'updated_at'
        ]

    def get_verification_details(self, obj):
        if obj.verification_status == Vendor.VerificationStatus.VERIFIED:
            return f"Verified by {obj.verified_by.email if obj.verified_by else 'system'}"
        elif obj.verification_status == Vendor.VerificationStatus.REJECTED:
            return f"Rejected: {obj.verification_notes or 'No reason provided'}"
        return "Pending verification"

class AdminProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for admin profile with access level information
    """
    user = UserSerializer(read_only=True)
    access_level_display = serializers.CharField(
        source='get_access_level_display',
        read_only=True
    )

    class Meta:
        model = AdminProfile
        fields = [
            'user', 'access_level', 'access_level_display', 'department',
            'notes', 'can_manage_users', 'can_manage_vendors',
            'can_manage_content', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

# ==================== VENDOR EMPLOYEE SERIALIZERS ====================

class VendorEmployeeSerializer(serializers.ModelSerializer):
    """
    Serializer for vendor employee data with role information
    """
    user = UserSerializer(read_only=True)
    vendor = serializers.PrimaryKeyRelatedField(
        queryset=Vendor.objects.all(),
        required=False
    )
    role_display = serializers.CharField(
        source='get_role_display',
        read_only=True
    )

    class Meta:
        model = VendorEmployee
        fields = [
            'user', 'vendor', 'role', 'role_display', 'department',
            'hire_date', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

# ==================== ADDRESS SERIALIZERS ====================

class AddressSerializer(serializers.ModelSerializer):
    """
    Serializer for user addresses with type information
    """
    type_display = serializers.CharField(
        source='get_type_display',
        read_only=True
    )

    class Meta:
        model = Address
        fields = [
            'id', 'type', 'type_display', 'recipient_name',
            'street', 'city', 'state', 'country', 'postal_code',
            'phone_number', 'is_default', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        if data.get('is_default'):
            required_fields = ['street', 'city', 'country', 'postal_code']
            if not all(data.get(field) for field in required_fields):
                raise serializers.ValidationError(
                    "Default address must include street, city, country and postal code"
                )
        return data

# ==================== ADMIN MANAGEMENT SERIALIZERS ====================

class AdminUserManagementSerializer(UserSerializer):
    """
    Extended user serializer for admin management with additional fields
    """
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['is_active', 'is_staff', 'is_superuser']
        read_only_fields = ['date_joined', 'last_login']

class AdminVendorManagementSerializer(VendorProfileSerializer):
    """
    Extended vendor serializer for admin management with verification controls
    """
    verification_notes = serializers.CharField(required=False, allow_blank=True)
    verified_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.Role.ADMIN),
        required=False
    )

    class Meta(VendorProfileSerializer.Meta):
        read_only_fields = [
            f for f in VendorProfileSerializer.Meta.read_only_fields
            if f not in ['verification_status', 'verification_notes', 'verified_by']
        ]

# ==================== REGISTRATION SERIALIZERS ====================

class CustomerRegistrationSerializer(serializers.Serializer):
    """
    Combined serializer for customer registration (user + profile)
    """
    user = UserCreateSerializer()
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_serializer = UserCreateSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save(role=User.Role.CUSTOMER)
        
        return Customer.objects.create(user=user, **validated_data)

class VendorRegistrationSerializer(serializers.Serializer):
    """
    Combined serializer for vendor registration (user + business)
    """
    user = UserCreateSerializer()
    business_name = serializers.CharField()
    business_email = serializers.EmailField()

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_serializer = UserCreateSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save(role=User.Role.VENDOR)
        
        return Vendor.objects.create(
            user=user,
            verification_status=Vendor.VerificationStatus.PENDING,
            **validated_data
        )

class VendorEmployeeProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for vendor employee data with role information
    """
    user = UserSerializer(read_only=True)
    vendor = serializers.PrimaryKeyRelatedField(
        queryset=Vendor.objects.all(),
        required=False
    )
    role_display = serializers.CharField(
        source='get_role_display',
        read_only=True
    )

    class Meta:
        model = VendorEmployee
        fields = [
            'user', 'vendor', 'role', 'role_display', 'department',
            'hire_date', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']