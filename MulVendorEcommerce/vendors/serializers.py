# from rest_framework import serializers
# from .models import VendorDashboard, VendorPayment, VendorWithdrawalRequest, VendorVerification
# from Users.serializers import VendorSerializer, UserSerializer
# from django.utils import timezone
# from django.db.models import Sum
# from products.models import ProductReview

# class VendorDashboardSerializer(serializers.ModelSerializer):
#     vendor = VendorSerializer(read_only=True)
#     last_login = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
#     last_sale = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
#     verification_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    
#     # Calculated fields
#     total_earnings = serializers.SerializerMethodField()
#     pending_withdrawals = serializers.SerializerMethodField()

#     class Meta:
#         model = VendorDashboard
#         fields = [
#             'vendor', 'total_sales', 'total_earnings', 'total_orders', 
#             'inventory_count', 'average_rating', 'last_login', 'last_sale',
#             'performance_score', 'is_verified', 'verification_date',
#             'pending_withdrawals'
#         ]
#         read_only_fields = fields

#     def get_total_earnings(self, obj):
#         # Calculate total earnings after deducting processed withdrawals
#         processed_withdrawals = VendorWithdrawalRequest.objects.filter(
#             vendor=obj.vendor,
#             status__in=['processed', 'approved']
#         ).aggregate(total=Sum('amount'))['total'] or 0
#         return obj.total_sales - processed_withdrawals

#     def get_pending_withdrawals(self, obj):
#         # Sum of pending withdrawal requests
#         return VendorWithdrawalRequest.objects.filter(
#             vendor=obj.vendor,
#             status='pending'
#         ).aggregate(total=Sum('amount'))['total'] or 0

# class VendorPaymentSerializer(serializers.ModelSerializer):
#     vendor = VendorSerializer(read_only=True)
#     payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
#     status_display = serializers.CharField(source='get_status_display', read_only=True)
#     processed_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
#     created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
#     updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

#     class Meta:
#         model = VendorPayment
#         fields = [
#             'id', 'vendor', 'amount', 'payment_method', 'payment_method_display',
#             'reference', 'status', 'status_display', 'period_start', 'period_end',
#             'processed_at', 'created_at', 'updated_at'
#         ]
#         read_only_fields = ['id', 'created_at', 'updated_at', 'processed_at']

#     def validate(self, data):
#         if data['period_start'] > data['period_end']:
#             raise serializers.ValidationError("Period end must be after period start")
#         return data

# class VendorWithdrawalRequestSerializer(serializers.ModelSerializer):
#     vendor = VendorSerializer(read_only=True)
#     status_display = serializers.CharField(source='get_status_display', read_only=True)
#     payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
#     created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
#     updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
#     processed_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
#     available_balance = serializers.SerializerMethodField()

#     class Meta:
#         model = VendorWithdrawalRequest
#         fields = [
#             'id', 'vendor', 'amount', 'available_balance', 'payment_method',
#             'payment_method_display', 'account_details', 'status', 'status_display',
#             'notes', 'created_at', 'updated_at', 'processed_at'
#         ]
#         read_only_fields = [
#             'id', 'created_at', 'updated_at', 'processed_at', 'available_balance'
#         ]

#     def get_available_balance(self, obj):
#         dashboard = obj.vendor.dashboard
#         pending_withdrawals = VendorWithdrawalRequest.objects.filter(
#             vendor=obj.vendor,
#             status='pending'
#         ).exclude(id=obj.id).aggregate(total=Sum('amount'))['total'] or 0
#         return dashboard.total_sales - pending_withdrawals

#     def validate_amount(self, value):
#         request = self.context.get('request')
#         if request and hasattr(request.user, 'vendor'):
#             dashboard = request.user.vendor.dashboard
#             pending_withdrawals = VendorWithdrawalRequest.objects.filter(
#                 vendor=request.user.vendor,
#                 status='pending'
#             ).aggregate(total=Sum('amount'))['total'] or 0
            
#             if value > (dashboard.total_sales - pending_withdrawals):
#                 raise serializers.ValidationError(
#                     "Withdrawal amount exceeds available balance after accounting for pending withdrawals"
#                 )
#         return value

#     def create(self, validated_data):
#         request = self.context.get('request')
#         if request and hasattr(request.user, 'vendor'):
#             validated_data['vendor'] = request.user.vendor
#         return super().create(validated_data)

# class VendorVerificationDocumentSerializer(serializers.Serializer):
#     document_type = serializers.CharField(max_length=50, required=True)
#     document_front = serializers.ImageField(required=True)
#     document_back = serializers.ImageField(required=False)
#     additional_documents = serializers.ListField(
#         child=serializers.FileField(),
#         required=False
#     )

# class VendorVerificationSerializer(serializers.ModelSerializer):
#     vendor = VendorSerializer(read_only=True)
#     status_display = serializers.CharField(source='get_status_display', read_only=True)
#     document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
#     document_front_url = serializers.SerializerMethodField()
#     document_back_url = serializers.SerializerMethodField()
#     additional_documents_urls = serializers.SerializerMethodField()
#     reviewed_by = UserSerializer(read_only=True)
#     submitted_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
#     reviewed_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

#     class Meta:
#         model = VendorVerification
#         fields = [
#             'id', 'vendor', 'status', 'status_display', 'document_type', 'document_type_display',
#             'document_front', 'document_front_url', 'document_back', 'document_back_url',
#             'additional_documents', 'additional_documents_urls', 'rejection_reason',
#             'submitted_at', 'reviewed_at', 'reviewed_by'
#         ]
#         read_only_fields = [
#             'id', 'submitted_at', 'reviewed_at', 'document_front_url',
#             'document_back_url', 'additional_documents_urls', 'reviewed_by'
#         ]

#     def get_document_front_url(self, obj):
#         request = self.context.get('request')
#         if obj.document_front and request:
#             return request.build_absolute_uri(obj.document_front.url)
#         return None

#     def get_document_back_url(self, obj):
#         request = self.context.get('request')
#         if obj.document_back and request:
#             return request.build_absolute_uri(obj.document_back.url)
#         return None

#     def get_additional_documents_urls(self, obj):
#         request = self.context.get('request')
#         if obj.additional_documents and request:
#             return [request.build_absolute_uri(doc['url']) for doc in obj.additional_documents if doc.get('url')]
#         return []

#     def update(self, instance, validated_data):
#         if 'status' in validated_data:
#             if validated_data['status'] == 'approved':
#                 instance.approve(self.context['request'].user)
#             elif validated_data['status'] == 'rejected' and 'rejection_reason' in validated_data:
#                 instance.reject(self.context['request'].user, validated_data['rejection_reason'])
#             else:
#                 instance.status = validated_data['status']
#                 instance.save()
#         return instance