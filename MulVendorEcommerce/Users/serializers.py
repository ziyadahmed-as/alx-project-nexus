from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Customer, Vendor, AdminProfile, VendorEmployee, Address

User = get_user_model()


# -------------------------------
# JWT Token Serializer Override
# -------------------------------
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['email'] = user.email
        token['role'] = user.role
        token['is_verified'] = user.is_verified
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = {
            'id': str(self.user.id),
            'username': self.user.username,
            'email': self.user.email,
            'role': self.user.role,
            'is_verified': self.user.is_verified
        }
        return data


# -------------------------------
# User Serializer
# -------------------------------
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'password', 'phone_number', 'role', 'is_verified']
        read_only_fields = ['is_verified']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


# -------------------------------
# Customer Serializer
# -------------------------------
class CustomerSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Customer
        fields = '__all__'

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data['role'] = 'CUSTOMER'
        user = UserSerializer().create(user_data)
        return Customer.objects.create(user=user, **validated_data)


# -------------------------------
# Vendor Serializer
# -------------------------------
class VendorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Vendor
        fields = '__all__'
        read_only_fields = ['is_approved', 'store_rating']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
            if request.user.role != 'VENDOR':
                request.user.role = 'VENDOR'
                request.user.save()
            return super().create(validated_data)
        raise serializers.ValidationError("Authentication required to create a vendor.")


# -------------------------------
# AdminProfile Serializer
# -------------------------------
class AdminProfileSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role='ADMIN'))

    class Meta:
        model = AdminProfile
        fields = '__all__'

    def validate_user(self, value):
        if value.role != 'ADMIN':
            raise serializers.ValidationError("User must be an admin.")
        return value


# -------------------------------
# VendorEmployee Serializer
# -------------------------------
class VendorEmployeeSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    vendor = serializers.PrimaryKeyRelatedField(queryset=Vendor.objects.all())

    class Meta:
        model = VendorEmployee
        fields = '__all__'

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data['role'] = 'VENDOR'
        user = UserSerializer().create(user_data)
        validated_data['user'] = user

        request = self.context.get('request')
        if request and request.user.role == 'VENDOR':
            validated_data['vendor'] = request.user.vendor

        return VendorEmployee.objects.create(**validated_data)


# -------------------------------
# Address Serializer
# -------------------------------
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'
        read_only_fields = ['user']

    def validate(self, attrs):
        if attrs.get('is_default') and not (attrs.get('street') and attrs.get('city')):
            raise serializers.ValidationError("Default address must include both street and city.")
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
            if validated_data.get('is_default'):
                Address.objects.filter(user=request.user).update(is_default=False)
            return super().create(validated_data)
        raise serializers.ValidationError("User authentication is required.")
