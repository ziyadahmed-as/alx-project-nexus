from rest_framework import generics, permissions, status, viewsets, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone

from .models import User, CustomerProfile, AdminProfile, Vendor, VendorEmployee, Address
from .serializers import (
    UserSerializer,
    CustomerProfileSerializer,
    VendorProfileSerializer,
    AdminProfileSerializer,
    VendorEmployeeSerializer,
    AddressSerializer,
    UserRegistrationSerializer,
    UserLoginSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer
)

class AuthViewSet(viewsets.GenericViewSet):
    """
    Authentication endpoints for user registration, login, and password management
    """
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == 'register':
            return UserRegistrationSerializer
        elif self.action == 'login':
            return UserLoginSerializer
        elif self.action == 'password_reset':
            return PasswordResetSerializer
        elif self.action == 'password_reset_confirm':
            return PasswordResetConfirmSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        """Authenticate user and return JWT tokens"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # Update last active timestamp
        user.last_active = timezone.now()
        user.save(update_fields=['last_active'])
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        })

    @action(detail=False, methods=['post'], url_path='register')
    def register(self, request):
        """Register a new user with profile creation"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            user = serializer.save()
            role = serializer.validated_data.get('role', User.Role.CUSTOMER)
            
            # Create appropriate profile based on role
            if role == User.Role.CUSTOMER:
                CustomerProfile.objects.create(user=user)
            elif role == User.Role.VENDOR:
                Vendor.objects.create(user=user)
            elif role == User.Role.ADMIN:
                # Only superusers can create admin accounts through registration
                if not user.is_superuser:
                    raise PermissionDenied("Admin registration not allowed")
                AdminProfile.objects.create(user=user)

            # Generate tokens for immediate login
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='password-reset')
    def password_reset(self, request):
        """Initiate password reset process"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # In a real implementation, you would send an email here
        return Response(
            {'detail': 'Password reset link has been sent if email exists'},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'], url_path='password-reset-confirm')
    def password_reset_confirm(self, request):
        """Complete password reset process"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # In a real implementation, you would update the password here
        return Response(
            {'detail': 'Password has been reset successfully'},
            status=status.HTTP_200_OK
        )

class UserViewSet(viewsets.GenericViewSet,
                 mixins.RetrieveModelMixin,
                 mixins.UpdateModelMixin,
                 mixins.ListModelMixin):
    """
    User management endpoints
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_staff:
            return User.objects.filter(pk=self.request.user.pk)
        return super().get_queryset()

    @action(detail=False, methods=['get', 'patch'])
    def me(self, request):
        """Retrieve or update current user's profile"""
        if request.method == 'GET':
            serializer = CustomerProfile(request.user)
            return Response(serializer.data)
        
        serializer = self.get_serializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(CustomerProfile(request.user).data)

class ProfileViewSet(viewsets.GenericViewSet,
                    mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin):
    """
    Base profile viewset with common functionality
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile = getattr(self.request.user, self.profile_attr, None)
        if not profile:
            raise PermissionDenied(f"No {self.profile_attr.replace('_', ' ')} found")
        return profile

class CustomerProfileViewSet(ProfileViewSet):
    """
    Customer profile management
    """
    serializer_class = CustomerProfileSerializer
    profile_attr = 'customer_profile'

class VendorProfileViewSet(ProfileViewSet):
    """
    Vendor profile management
    """
    serializer_class = VendorProfileSerializer
    profile_attr = 'vendor'

class AdminProfileViewSet(ProfileViewSet):
    """
    Admin profile management
    """
    serializer_class = AdminProfileSerializer
    permission_classes = [permissions.IsAdminUser]
    profile_attr = 'admin_profile'

class VendorEmployeeViewSet(viewsets.ModelViewSet):
    """
    Vendor employee management
    """
    serializer_class = VendorEmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.VENDOR:
            return VendorEmployee.objects.filter(vendor__user=user)
        elif user.role == User.Role.VENDOR_STAFF:
            return VendorEmployee.objects.filter(user=user)
        return VendorEmployee.objects.none()

    def perform_create(self, serializer):
        if self.request.user.role != User.Role.VENDOR:
            raise PermissionDenied("Only vendors can create employees")
        vendor = get_object_or_404(Vendor, user=self.request.user)
        serializer.save(vendor=vendor)

class AddressViewSet(viewsets.ModelViewSet):
    """
    User address management
    """
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        if serializer.validated_data.get('is_default', False):
            Address.objects.filter(
                user=self.request.user,
                address_type=serializer.validated_data['address_type'],
                is_default=True
            ).update(is_default=False)
        serializer.save(user=self.request.user)

class AdminUserManagementViewSet(viewsets.ModelViewSet):
    """
    Admin user management
    """
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['role', 'is_active', 'is_verified']
    search_fields = ['email', 'first_name', 'last_name']

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify a user account"""
        user = self.get_object()
        user.is_verified = True
        user.save(update_fields=['is_verified'])
        return Response(
            {'status': 'User verified successfully'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def make_admin(self, request, pk=None):
        """Promote user to admin"""
        user = self.get_object()
        if user.role == User.Role.ADMIN:
            return Response(
                {'status': 'User is already an admin'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.role = User.Role.ADMIN
        user.is_staff = True
        user.save(update_fields=['role', 'is_staff'])
        AdminProfile.objects.get_or_create(user=user)
            
        return Response(
            {'status': 'User promoted to admin successfully'},
            status=status.HTTP_200_OK
        )

class AdminVendorManagementViewSet(viewsets.ModelViewSet):
    """
    Admin vendor management
    """
    queryset = Vendor.objects.all().order_by('-created_at')
    serializer_class = VendorProfileSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['verification_status', 'business_type']
    search_fields = ['user__email', 'company_registration_number']

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify a vendor"""
        vendor = self.get_object()
        vendor.verification_status = Vendor.VerificationStatus.VERIFIED
        vendor.save(update_fields=['verification_status'])
        return Response(
            {'status': 'Vendor verified successfully'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        """Suspend a vendor"""
        vendor = self.get_object()
        vendor.verification_status = Vendor.VerificationStatus.SUSPENDED
        vendor.save(update_fields=['verification_status'])
        return Response(
            {'status': 'Vendor suspended successfully'},
            status=status.HTTP_200_OK
        )