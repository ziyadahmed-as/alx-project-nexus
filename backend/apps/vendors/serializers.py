from rest_framework import serializers
from .models import VendorProfile, KYCVerification, KYCDocument
from apps.users.serializers import UserSerializer

class VendorProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = VendorProfile
        fields = '__all__'
        read_only_fields = ['user', 'status', 'verified_by', 'verified_at', 
                           'total_sales', 'total_orders', 'rating', 'is_active',
                           'suspended_at', 'suspended_by', 'suspension_reason']

class VendorVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorProfile
        fields = ['status', 'verification_notes']

class KYCDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYCDocument
        fields = ['id', 'document_type', 'file', 'original_filename', 
                  'file_size', 'uploaded_at', 'verified']
        read_only_fields = ['id', 'original_filename', 'file_size', 'uploaded_at', 'verified']

class KYCVerificationSerializer(serializers.ModelSerializer):
    documents = KYCDocumentSerializer(many=True, read_only=True)
    
    class Meta:
        model = KYCVerification
        fields = ['id', 'status', 'full_name', 'date_of_birth', 'nationality',
                  'address', 'city', 'country', 'postal_code', 'submitted_at',
                  'reviewed_at', 'admin_notes', 'rejection_reason', 'documents']
        read_only_fields = ['id', 'status', 'submitted_at', 'reviewed_at', 
                           'admin_notes', 'rejection_reason']
