from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import CustomerProfile, Vendor, AdminProfile, VendorEmployee, Address

User = get_user_model()

# ----------------------
# Utility Functions
# ----------------------
def unique_for(model, field_name, message=None):
    return UniqueValidator(
        queryset=model.objects.all(),
        message=message or _(f"This {field_name.replace('_', ' ')} is already in use.")
    )

def validate_password_match(attrs):
    if attrs.get('password') != attrs.get('password_confirm'):
        raise serializers.ValidationError({'password_confirm': _("Passwords do not match")})
    return attrs

# ----------------------
# User Serializers
# ----------------------
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, style={'input_type': 'password'})
    email = serializers.EmailField(validators=[unique_for(User, 'email')])

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'password', 'password_confirm', 'role']
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'phone_number': {'validators': [unique_for(User, 'phone_number')]}
        }

    def validate(self, attrs):
        attrs = validate_password_match(attrs)
        if attrs.get('role') == User.Role.ADMIN and not self.context.get('is_admin_request'):
            raise serializers.ValidationError({'role': _("Admin registration is restricted.")})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'})

    def validate(self, attrs):
        user = authenticate(request=self.context.get('request'), **attrs)
        if not user:
            raise serializers.ValidationError(_("Invalid credentials"))
        if not user.is_active:
            raise serializers.ValidationError(_("Account is disabled."))
        return {'user': user}

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'phone_number', 
                 'role', 'role_display', 'is_active', 'is_verified', 'last_active']
        read_only_fields = fields

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

# ----------------------
# Profile Serializers
# ----------------------
class BaseProfileSerializer(serializers.ModelSerializer):
    def get_age(self, obj):
        if not obj.date_of_birth:
            return None
        today = timezone.now().date()
        return today.year - obj.date_of_birth.year - (
            (today.month, today.day) < (obj.date_of_birth.month, obj.date_of_birth.day)
        )

class CustomerProfileSerializer(BaseProfileSerializer):
    user = UserSerializer(read_only=True)
    age = serializers.SerializerMethodField()

    class Meta:
        model = CustomerProfile
        fields = ['id', 'user', 'date_of_birth', 'age', 'profile_picture', 'preferred_language']

class VendorProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Vendor
        fields = ['email', 'company_name', 'business_email', 'company_registration_number', 
                 'verification_status', 'business_type', 'tax_identification_number']
        extra_kwargs = {
            'business_email': {'validators': [unique_for(Vendor, 'business_email')]},
            'company_registration_number': {'validators': [unique_for(Vendor, 'company_registration_number')]}
        }

class AdminProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    department_display = serializers.CharField(source='get_department_display', read_only=True)

    class Meta:
        model = AdminProfile
        fields = ['user', 'department', 'department_display', 'position', 'access_level']

# ----------------------
# Other Serializers
# ----------------------
class VendorEmployeeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = VendorEmployee
        fields = ['user', 'vendor', 'employee_id', 'role', 'role_display', 'department', 'is_active']

class AddressSerializer(serializers.ModelSerializer):
    address_type_display = serializers.CharField(source='get_address_type_display', read_only=True)

    class Meta:
        model = Address
        fields = ['user', 'address_type', 'address_type_display', 'street_address', 
                 'city', 'state', 'postal_code', 'country', 'is_default']

    def validate(self, attrs):
        if attrs.get('is_default'):
            Address.objects.filter(
                user=attrs['user'],
                address_type=attrs['address_type'],
                is_default=True
            ).update(is_default=False)
        return attrs

# ----------------------
# Password Serializers
# ----------------------

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(min_length=8, style={'input_type': 'password'})
    new_password_confirm = serializers.CharField(style={'input_type': 'password'})
    token = serializers.CharField()

    def validate(self, attrs):
        return validate_password_match(attrs)