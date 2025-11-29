from rest_framework import serializers
from .models import VendorProfile
from apps.users.serializers import UserSerializer

class VendorProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = VendorProfile
        fields = '__all__'
        read_only_fields = ['user', 'status', 'verified_by', 'verified_at', 
                           'total_sales', 'total_orders', 'rating']

class VendorVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorProfile
        fields = ['status', 'verification_notes']
