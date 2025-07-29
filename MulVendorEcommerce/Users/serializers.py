from rest_framework import serializers
from .models import User, Customer, Vendor, AdminProfile, VendorEmployee, Address
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

# this Token Obtain with Pair Serializer is used to add custom claims to the JWT token
# such as user role, which can be used for permission checks in views.
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        return token
    
# User Serializer for the User model
# This serializer is used to serialize user data, including custom fields like phone number and role.
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'phone_number', 'role', 'is_verified']
        read_only_fields = ['is_verified']

# This serializer is used to serialize the AdminProfile model.
class CustomerSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    
    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = ['user']

# VendorSerializer is used to serialize the Vendor model.
# It includes the UserSerializer to provide user details and read-only fields for certain attributes.
class VendorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Vendor
        fields = '__all__'
        read_only_fields = ['user', 'is_approved', 'store_rating']

# Vendor Employee Serializer 
class VendorEmployeeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    vendor = VendorSerializer(read_only=True)
    
    class Meta:
        model = VendorEmployee
        fields = '__all__'
# address serializer for the Address model
# It includes validation to ensure that if an address is marked as default, it must have a
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'
        read_only_fields = ['user']

    def validate(self, attrs):
        if attrs.get('is_default') and not (attrs.get('street') and attrs.get('city')):
            raise serializers.ValidationError("Default address must have street and city")
        return attrs