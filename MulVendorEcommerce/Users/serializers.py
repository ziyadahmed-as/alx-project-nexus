from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils import timezone
from .models import Customer, Vendor, AdminProfile, VendorEmployee, VendorProfile, Address

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
            'is_verified', 'last_active', 'created_at', 'updated_at'
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
        fields = ['email', 'username', 'password', 'password_confirmation', 'phone_number', 'role']
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': False},
            'role': {'required': False}
        }

    def validate(self, data):
        if data['password'] != data['password_confirmation']:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirmation')
        role = validated_data.pop('role', User.Role.CUSTOMER)
        user = User.objects.create_user(role=role, **validated_data)
        return user

# ==================== PROFILE SERIALIZERS ====================

class UserDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for user information with related profiles
    """
    customer_profile = serializers.SerializerMethodField()
    vendor = serializers.SerializerMethodField()
    admin_profile = serializers.SerializerMethodField()
    vendor_employee = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'phone_number', 'role',
            'is_verified', 'last_active', 'created_at', 'updated_at',
            'customer_profile', 'vendor', 'admin_profile', 'vendor_employee'
        ]
        read_only_fields = fields

    def get_customer_profile(self, obj):
        if hasattr(obj, 'customer_profile'):
            return CustomerProfileSerializer(obj.customer_profile).data
        return None

    def get_vendor(self, obj):
        if hasattr(obj, 'vendor'):
            return VendorSerializer(obj.vendor).data
        return None

    def get_admin_profile(self, obj):
        if hasattr(obj, 'admin_profile'):
            return AdminProfileSerializer(obj.admin_profile).data
        return None

    def get_vendor_employee(self, obj):
        if hasattr(obj, 'vendor_employee'):
            return VendorEmployeeSerializer(obj.vendor_employee).data
        return None

class CustomerProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for customer profile data
    """
    user = UserSerializer(read_only=True)
    age = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = [
            'user', 'date_of_birth', 'profile_picture', 'age',
            'preferred_language', 'newsletter_subscription',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_age(self, obj):
        if obj.date_of_birth:
            today = timezone.now().date()
            return today.year - obj.date_of_birth.year - (
                (today.month, today.day) < (obj.date_of_birth.month, obj.date_of_birth.day)
            )
        return None

class VendorSerializer(serializers.ModelSerializer):
    """
    Serializer for vendor business information
    """
    user = UserSerializer(read_only=True)

    class Meta:
        model = Vendor
        fields = [
            'user', 'company_registration_number', 'tax_identification_number',
            'years_in_business', 'accepted_terms', 'terms_accepted_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class VendorProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for vendor profile with verification status
    """
    user = UserSerializer(read_only=True)
    verification_status_display = serializers.CharField(
        source='get_verification_status_display',
        read_only=True
    )

    class Meta:
        model = VendorProfile
        fields = [
            'user', 'business_name', 'business_address', 'business_location',
            'business_description', 'business_email', 'business_phone',
            'tax_id', 'store_logo', 'verification_status', 'verification_status_display',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'verification_status', 'verification_status_display',
            'created_at', 'updated_at', 'business_location'
        ]

    def validate_business_address(self, value):
        if value and value.address_type != Address.AddressType.BUSINESS:
            raise serializers.ValidationError(
                "Address must be of type BUSINESS")
        return value

class AdminProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for admin profile with access level information
    """
    user = UserSerializer(read_only=True)

    class Meta:
        model = AdminProfile
        fields = [
            'user', 'department', 'position', 'access_level',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

# ==================== VENDOR EMPLOYEE SERIALIZERS ====================

class VendorEmployeeSerializer(serializers.ModelSerializer):
    """
    Serializer for vendor employee data with role information
    """
    user = UserSerializer(read_only=True)
    vendor = serializers.PrimaryKeyRelatedField(queryset=Vendor.objects.all())
    role_display = serializers.CharField(
        source='get_role_display',
        read_only=True
    )

    class Meta:
        model = VendorEmployee
        fields = [
            'user', 'vendor', 'employee_id', 'role', 'role_display',
            'department', 'is_active', 'hire_date', 'termination_date',
            'permissions', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

# ==================== ADDRESS SERIALIZERS ====================

class AddressSerializer(serializers.ModelSerializer):
    """
    Serializer for user addresses with type information
    """
    address_type_display = serializers.CharField(
        source='get_address_type_display',
        read_only=True
    )

    class Meta:
        model = Address
        fields = [
            'id', 'user', 'address_type', 'address_type_display', 'recipient_name',
            'street_address', 'city', 'state', 'country', 'postal_code',
            'location', 'phone_number', 'is_default', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'location']

    def validate(self, data):
        if data.get('is_default') and data.get('address_type') == Address.AddressType.BUSINESS:
            raise serializers.ValidationError(
                "Business addresses cannot be set as default")
        return data

# ==================== ADMIN MANAGEMENT SERIALIZERS ====================

class AdminUserManagementSerializer(UserSerializer):
    """
    Extended user serializer for admin management with additional fields
    """
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['is_active', 'is_staff', 'is_superuser']

class AdminVendorManagementSerializer(VendorProfileSerializer):
    """
    Extended vendor serializer for admin management with verification controls
    """
    class Meta(VendorProfileSerializer.Meta):
        read_only_fields = [
            f for f in VendorProfileSerializer.Meta.read_only_fields
            if f != 'verification_status'
        ]

# ==================== REGISTRATION SERIALIZERS ====================

class CustomerRegistrationSerializer(serializers.Serializer):
    """
    Combined serializer for customer registration (user + profile)
    """
    user = UserCreateSerializer()
    date_of_birth = serializers.DateField(required=False, allow_null=True)

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
    company_registration_number = serializers.CharField()
    tax_identification_number = serializers.CharField()

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_serializer = UserCreateSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save(role=User.Role.VENDOR)
        
        # Create both Vendor and VendorProfile
        vendor = Vendor.objects.create(user=user, **validated_data)
        VendorProfile.objects.create(
            user=user,
            business_name=validated_data['business_name'],
            business_email=validated_data['business_email'],
            verification_status=VendorProfile.VerificationStatus.PENDING
        )
        return vendor

class VendorEmployeeRegistrationSerializer(serializers.Serializer):
    """
    Serializer for vendor employee registration
    """
    user = UserCreateSerializer()
    vendor_id = serializers.UUIDField()
    role = serializers.ChoiceField(choices=VendorEmployee.EmployeeRole.choices)
    department = serializers.CharField(required=False)

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        vendor_id = validated_data.pop('vendor_id')
        
        user_serializer = UserCreateSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save(role=User.Role.VENDOR_STAFF)
        
        vendor = Vendor.objects.get(id=vendor_id)
        return VendorEmployee.objects.create(
            user=user,
            vendor=vendor,
            **validated_data
        )