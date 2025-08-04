from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.core.cache import cache
from django.conf import settings

from .models import Customer, Vendor, AdminProfile, VendorEmployee, VendorProfile, Address
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserSerializer,
    UserCreateSerializer,
    UserDetailSerializer,
    CustomerProfileSerializer,
    VendorSerializer,
    VendorProfileSerializer,
    AdminProfileSerializer,
    VendorEmployeeSerializer,
    AddressSerializer,
    AdminUserManagementSerializer,
    AdminVendorManagementSerializer,
    CustomerRegistrationSerializer,
    VendorRegistrationSerializer,
    VendorEmployeeRegistrationSerializer
)

User = get_user_model()

# Cache constants
CACHE_TTL = getattr(settings, 'CACHE_TTL', 60 * 15)  # 15 minutes default
USER_CACHE_KEY = "user_{id}"
CUSTOMER_PROFILE_CACHE_KEY = "customer_profile_{id}"
VENDOR_CACHE_KEY = "vendor_{id}"
VENDOR_PROFILE_CACHE_KEY = "vendor_profile_{id}"
ADMIN_PROFILE_CACHE_KEY = "admin_profile_{id}"
VENDOR_EMPLOYEES_CACHE_KEY = "vendor_{id}_employees"
ADDRESSES_CACHE_KEY = "user_{id}_addresses"

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200 and 'email' in request.data:
            user = User.objects.filter(email=request.data['email']).first()
            if user:
                # Clear user-related caches on login
                cache.delete(USER_CACHE_KEY.format(id=user.id))
                cache.delete(CUSTOMER_PROFILE_CACHE_KEY.format(id=user.id))
                cache.delete(VENDOR_CACHE_KEY.format(id=user.id))
                cache.delete(VENDOR_PROFILE_CACHE_KEY.format(id=user.id))
                cache.delete(ADMIN_PROFILE_CACHE_KEY.format(id=user.id))
        return response

class UserRegistrationView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.request.path.endswith('customer/'):
            return CustomerRegistrationSerializer
        elif self.request.path.endswith('vendor/'):
            return VendorRegistrationSerializer
        elif self.request.path.endswith('vendor-employee/'):
            return VendorEmployeeRegistrationSerializer
        return super().get_serializer_class()

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            instance = serializer.save()
            
            # Clear relevant caches after registration
            if isinstance(instance, Customer):
                cache_key = CUSTOMER_PROFILE_CACHE_KEY.format(id=instance.user.id)
                cache.delete(cache_key)
            elif isinstance(instance, Vendor):
                cache_key = VENDOR_CACHE_KEY.format(id=instance.user.id)
                cache.delete(cache_key)
                cache_key = VENDOR_PROFILE_CACHE_KEY.format(id=instance.user.id)
                cache.delete(cache_key)
            elif isinstance(instance, VendorEmployee):
                cache_key = VENDOR_EMPLOYEES_CACHE_KEY.format(id=instance.vendor.id)
                cache.delete(cache_key)
            
            # Determine appropriate response serializer
            if isinstance(instance, Customer):
                response_serializer = CustomerProfileSerializer(instance)
            elif isinstance(instance, Vendor):
                response_serializer = VendorSerializer(instance)
            elif isinstance(instance, VendorEmployee):
                response_serializer = VendorEmployeeSerializer(instance)
            else:
                response_serializer = UserSerializer(instance.user)
            
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserDetailSerializer

    def get_object(self):
        cache_key = USER_CACHE_KEY.format(id=self.request.user.id)
        user = cache.get(cache_key)
        
        if not user:
            user = self.request.user
            cache.set(cache_key, user, CACHE_TTL)
        return user

    def perform_update(self, serializer):
        instance = serializer.save()
        # Update cache
        cache_key = USER_CACHE_KEY.format(id=instance.id)
        cache.set(cache_key, instance, CACHE_TTL)
        return instance

class CustomerProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = CustomerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        if not hasattr(self.request.user, 'customer_profile'):
            raise PermissionDenied("Customer profile does not exist")
            
        cache_key = CUSTOMER_PROFILE_CACHE_KEY.format(id=self.request.user.id)
        profile = cache.get(cache_key)
        
        if not profile:
            profile = self.request.user.customer_profile
            cache.set(cache_key, profile, CACHE_TTL)
        return profile

    def perform_update(self, serializer):
        instance = serializer.save()
        # Update cache
        cache_key = CUSTOMER_PROFILE_CACHE_KEY.format(id=instance.user.id)
        cache.set(cache_key, instance, CACHE_TTL)
        return instance

class VendorView(generics.RetrieveUpdateAPIView):
    serializer_class = VendorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        if not hasattr(self.request.user, 'vendor'):
            raise PermissionDenied("Vendor profile does not exist")
            
        cache_key = VENDOR_CACHE_KEY.format(id=self.request.user.id)
        vendor = cache.get(cache_key)
        
        if not vendor:
            vendor = self.request.user.vendor
            cache.set(cache_key, vendor, CACHE_TTL)
        return vendor

    def perform_update(self, serializer):
        instance = serializer.save()
        # Update cache
        cache_key = VENDOR_CACHE_KEY.format(id=instance.user.id)
        cache.set(cache_key, instance, CACHE_TTL)
        return instance

class VendorProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = VendorProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        if not hasattr(self.request.user, 'vendor_profile'):
            raise PermissionDenied("Vendor profile does not exist")
            
        cache_key = VENDOR_PROFILE_CACHE_KEY.format(id=self.request.user.id)
        profile = cache.get(cache_key)
        
        if not profile:
            profile = self.request.user.vendor_profile
            cache.set(cache_key, profile, CACHE_TTL)
        return profile

    def perform_update(self, serializer):
        instance = serializer.save()
        # Update cache
        cache_key = VENDOR_PROFILE_CACHE_KEY.format(id=instance.user.id)
        cache.set(cache_key, instance, CACHE_TTL)
        return instance

class VendorVerificationView(generics.UpdateAPIView):
    queryset = VendorProfile.objects.select_related('user')
    serializer_class = AdminVendorManagementSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = 'pk'

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        vendor_profile = self.get_object()
        new_status = request.data.get('verification_status')
        
        if new_status not in [VendorProfile.VerificationStatus.VERIFIED, 
                            VendorProfile.VerificationStatus.REJECTED,
                            VendorProfile.VerificationStatus.SUSPENDED]:
            return Response(
                {"detail": "Invalid verification status"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            vendor_profile.verification_status = new_status
            if 'verification_notes' in request.data:
                vendor_profile.verification_notes = request.data['verification_notes']
            vendor_profile.save()

            # Update cache
            cache_key = VENDOR_PROFILE_CACHE_KEY.format(id=vendor_profile.user.id)
            cache.set(cache_key, vendor_profile, CACHE_TTL)

            serializer = self.get_serializer(vendor_profile)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AdminProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = AdminProfileSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_object(self):
        cache_key = ADMIN_PROFILE_CACHE_KEY.format(id=self.request.user.id)
        profile = cache.get(cache_key)
        
        if not profile:
            profile = get_object_or_404(AdminProfile, user=self.request.user)
            cache.set(cache_key, profile, CACHE_TTL)
        return profile

    def perform_update(self, serializer):
        instance = serializer.save()
        # Update cache
        cache_key = ADMIN_PROFILE_CACHE_KEY.format(id=instance.user.id)
        cache.set(cache_key, instance, CACHE_TTL)
        return instance

class VendorEmployeeViewSet(viewsets.ModelViewSet):
    serializer_class = VendorEmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.VENDOR:
            cache_key = VENDOR_EMPLOYEES_CACHE_KEY.format(id=user.id)
            employees = cache.get(cache_key)
            
            if not employees:
                employees = VendorEmployee.objects.filter(vendor__user=user).select_related('user', 'vendor')
                cache.set(cache_key, employees, CACHE_TTL)
            return employees
        elif user.role == User.Role.VENDOR_STAFF:
            return VendorEmployee.objects.filter(user=user).select_related('user', 'vendor')
        return VendorEmployee.objects.none()

    def perform_create(self, serializer):
        if self.request.user.role != User.Role.VENDOR:
            raise PermissionDenied("Only vendors can create employees")
        vendor = get_object_or_404(Vendor, user=self.request.user)
        instance = serializer.save(vendor=vendor)
        
        # Clear employees cache
        cache_key = VENDOR_EMPLOYEES_CACHE_KEY.format(id=vendor.id)
        cache.delete(cache_key)

    def perform_update(self, serializer):
        instance = serializer.save()
        # Clear employees cache
        cache_key = VENDOR_EMPLOYEES_CACHE_KEY.format(id=instance.vendor.id)
        cache.delete(cache_key)

    def perform_destroy(self, instance):
        vendor_id = instance.vendor.id
        instance.delete()
        # Clear employees cache
        cache_key = VENDOR_EMPLOYEES_CACHE_KEY.format(id=vendor_id)
        cache.delete(cache_key)

class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        cache_key = ADDRESSES_CACHE_KEY.format(id=self.request.user.id)
        addresses = cache.get(cache_key)
        
        if not addresses:
            addresses = Address.objects.filter(user=self.request.user)
            cache.set(cache_key, addresses, CACHE_TTL)
        return addresses

    def perform_create(self, serializer):
        # Ensure only one default address per type
        address_type = serializer.validated_data.get('address_type')
        if serializer.validated_data.get('is_default'):
            Address.objects.filter(
                user=self.request.user,
                address_type=address_type,
                is_default=True
            ).update(is_default=False)
        instance = serializer.save(user=self.request.user)
        # Clear addresses cache
        cache_key = ADDRESSES_CACHE_KEY.format(id=self.request.user.id)
        cache.delete(cache_key)

    def perform_update(self, serializer):
        instance = serializer.save()
        # Clear addresses cache
        cache_key = ADDRESSES_CACHE_KEY.format(id=self.request.user.id)
        cache.delete(cache_key)

    def perform_destroy(self, instance):
        user_id = instance.user.id
        instance.delete()
        # Clear addresses cache
        cache_key = ADDRESSES_CACHE_KEY.format(id=user_id)
        cache.delete(cache_key)

class AdminUserManagementViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = AdminUserManagementSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['role', 'is_active', 'is_verified']
    search_fields = ['email', 'username']
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        return super().get_queryset().select_related(
            'customer_profile', 'vendor', 'admin_profile', 'vendor_employee'
        )

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        user = self.get_object()
        if user.is_verified:
            return Response(
                {'status': 'User is already verified'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.is_verified = True
        user.save()
        
        # Clear user cache
        cache_key = USER_CACHE_KEY.format(id=user.id)
        cache.delete(cache_key)
        
        return Response(
            {'status': 'User verified successfully'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def make_admin(self, request, pk=None):
        user = self.get_object()
        if user.role == User.Role.ADMIN:
            return Response(
                {'status': 'User is already an admin'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.role = User.Role.ADMIN
        user.is_staff = True
        user.save()
        AdminProfile.objects.get_or_create(user=user)
        
        # Clear user cache
        cache_key = USER_CACHE_KEY.format(id=user.id)
        cache.delete(cache_key)
        
        return Response(
            {'status': 'User promoted to admin successfully'},
            status=status.HTTP_200_OK
        )

class AdminVendorManagementViewSet(viewsets.ModelViewSet):
    queryset = VendorProfile.objects.all().order_by('-created_at')
    serializer_class = AdminVendorManagementSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['verification_status', 'is_active']
    search_fields = ['business_name', 'user__email']
    http_method_names = ['get', 'post', 'patch', 'delete']

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        vendor_profile = self.get_object()
        if vendor_profile.is_active:
            return Response(
                {'status': 'Vendor is already active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        vendor_profile.is_active = True
        vendor_profile.save()
        
        # Update vendor profile cache
        cache_key = VENDOR_PROFILE_CACHE_KEY.format(id=vendor_profile.user.id)
        cache.set(cache_key, vendor_profile, CACHE_TTL)
        
        return Response(
            {'status': 'Vendor activated successfully'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        vendor_profile = self.get_object()
        if not vendor_profile.is_active:
            return Response(
                {'status': 'Vendor is already inactive'},
                status=status.HTTP_400_BAD_REQUEST
            )
        vendor_profile.is_active = False
        vendor_profile.save()
        
        # Update vendor profile cache
        cache_key = VENDOR_PROFILE_CACHE_KEY.format(id=vendor_profile.user.id)
        cache.set(cache_key, vendor_profile, CACHE_TTL)
        
        # Clear vendor employees cache
        employees_cache_key = VENDOR_EMPLOYEES_CACHE_KEY.format(id=vendor_profile.user.id)
        cache.delete(employees_cache_key)
        
        return Response(
            {'status': 'Vendor deactivated successfully'},
            status=status.HTTP_200_OK
        )