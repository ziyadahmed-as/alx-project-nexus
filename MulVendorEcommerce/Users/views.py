from rest_framework import generics, permissions, status, viewsets, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.core.cache import cache
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import User, CustomerProfile, Vendor, AdminProfile, VendorEmployee, Address
from .serializers import (
    UserSerializer,
    CustomerProfileSerializer,
    VendorProfileSerializer,
    AdminProfileSerializer,
    VendorEmployeeSerializer,
    AddressSerializer,
    UserRegistrationSerializer,
    UserLoginSerializer
)

class APIRootView(APIView):
    """Enhanced API root view showing all available endpoints"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, format=None):
        return Response({
            'auth': {
                'login': reverse('auth-login', request=request, format=format),
                'register': reverse('auth-register', request=request, format=format),
                'register_customer': reverse('auth-register-customer', request=request, format=format),
                'register_vendor': reverse('auth-register-vendor', request=request, format=format)
            },
            'users': reverse('user-list', request=request, format=format),
            'profiles': {
                'customers': reverse('customer-profile-list', request=request, format=format),
                'vendors': reverse('vendor-profile-list', request=request, format=format),
                'admins': reverse('admin-profile-list', request=request, format=format)
            },
            'vendor-employees': reverse('vendor-employee-list', request=request, format=format),
            'addresses': reverse('address-list', request=request, format=format),
            'admin': {
                'users': reverse('admin-user-list', request=request, format=format),
                'verify_user': reverse('admin-user-verify', request=request, format=format, kwargs={'pk': 1})[:-2],
                'cache_clear': reverse('cache-clear', request=request, format=format),
                'analytics': reverse('user-analytics', request=request, format=format)
            }
        })

class AuthViewSet(viewsets.GenericViewSet):
    """Authentication endpoints with JWT support"""
    permission_classes = [permissions.AllowAny]
    
    def get_serializer_class(self):
        return {
            'login': UserLoginSerializer,
            'register': UserRegistrationSerializer,
            'register_customer': UserRegistrationSerializer,
            'register_vendor': UserRegistrationSerializer
        }.get(self.action, UserRegistrationSerializer)
    
    @action(detail=False, methods=['post'], name='login')
    def login(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        if not user.is_active:
            return Response({'error': _('Account inactive')}, status=status.HTTP_403_FORBIDDEN)
        
        user.last_active = timezone.now()
        user.save(update_fields=['last_active'])
        
        return Response({
            'refresh': str(RefreshToken.for_user(user)),
            'access': str(RefreshToken.for_user(user).access_token),
            'user': UserSerializer(user, context={'request': request}).data
        })

    @transaction.atomic
    @action(detail=False, methods=['post'], name='register')
    def register(self, request):
        return self._register_user(request, request.data.copy())

    @transaction.atomic
    @action(detail=False, methods=['post'], url_path='register/customer', name='register-customer')
    def register_customer(self, request):
        data = request.data.copy()
        data['role'] = User.Role.CUSTOMER
        return self._register_user(request, data)

    @transaction.atomic
    @action(detail=False, methods=['post'], url_path='register/vendor', name='register-vendor')
    def register_vendor(self, request):
        data = request.data.copy()
        data['role'] = User.Role.VENDOR
        return self._register_user(request, data)

    def _register_user(self, request, data):
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        role = serializer.validated_data.get('role', User.Role.CUSTOMER)

        if role == User.Role.ADMIN:
            raise PermissionDenied(_("Admin registration restricted"))
        
        user = serializer.save()
        
        if role == User.Role.CUSTOMER:
            CustomerProfile.objects.get_or_create(user=user)
        elif role == User.Role.VENDOR:
            Vendor.objects.get_or_create(user=user)

        return Response({
            'refresh': str(RefreshToken.for_user(user)),
            'access': str(RefreshToken.for_user(user).access_token),
            'user': UserSerializer(user, context={'request': request}).data
        }, status=status.HTTP_201_CREATED)

class UserViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.ListModelMixin):
    """User profile management"""
    queryset = User.objects.select_related('customer_profile', 'vendor', 'admin_profile')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()
        if self.request.user.is_staff:
            return super().get_queryset()
        return super().get_queryset().filter(pk=self.request.user.pk)

    @action(detail=False, methods=['get', 'patch'], name='user-me')
    def me(self, request):
        if request.method == 'GET':
            return Response(self.get_serializer(request.user).data)
        
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class ProfileViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.UpdateModelMixin):
    """Base profile viewset"""
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile = getattr(self.request.user, self.profile_attr, None)
        if not profile:
            raise PermissionDenied(_(f"No {self.profile_attr.replace('_', ' ')} found"))
        return profile

class CustomerProfileViewSet(ProfileViewSet):
    serializer_class = CustomerProfileSerializer
    profile_attr = 'customer_profile'

class VendorProfileViewSet(ProfileViewSet):
    serializer_class = VendorProfileSerializer
    profile_attr = 'vendor'

class AdminProfileViewSet(ProfileViewSet):
    serializer_class = AdminProfileSerializer
    permission_classes = [permissions.IsAdminUser]
    profile_attr = 'admin_profile'

class VendorEmployeeViewSet(viewsets.ModelViewSet):
    """Vendor employee management"""
    queryset = VendorEmployee.objects.all()
    serializer_class = VendorEmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.VENDOR:
            return VendorEmployee.objects.filter(vendor__user=user)
        if user.role == User.Role.VENDOR_STAFF:
            return VendorEmployee.objects.filter(vendor=user.vendor_employee.vendor)
        return VendorEmployee.objects.none()

    @transaction.atomic
    def perform_create(self, serializer):
        if self.request.user.role != User.Role.VENDOR:
            raise PermissionDenied(_("Vendor access required"))
        serializer.save(vendor=self.request.user.vendor)

class AddressViewSet(viewsets.ModelViewSet):
    """User address management"""
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    @transaction.atomic
    def perform_create(self, serializer):
        if serializer.validated_data.get('is_default', False):
            Address.objects.filter(
                user=self.request.user,
                address_type=serializer.validated_data['address_type'],
                is_default=True
            ).update(is_default=False)
        serializer.save(user=self.request.user)

class AdminUserManagementViewSet(viewsets.ModelViewSet):
    """Admin user management"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

    @action(detail=True, methods=['post'], name='verify')
    def verify(self, request, pk=None):
        user = self.get_object()
        user.is_verified = True
        user.save(update_fields=['is_verified'])
        return Response({'status': _('User verified')})

class CacheManagementView(generics.GenericAPIView):
    """Cache management"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request):
        if not (user_id := request.data.get('user_id')):
            return Response({'error': _('User ID required')}, status=status.HTTP_400_BAD_REQUEST)
        
        cache.delete_many([f'user_{user_id}_customer', f'user_{user_id}_vendor'])
        return Response({'status': _('Cache cleared')})

class UserAnalyticsView(generics.GenericAPIView):
    """User analytics"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        return Response({
            'total': User.objects.count(),
            'active': User.objects.filter(is_active=True).count(),
            'customers': User.objects.filter(role=User.Role.CUSTOMER).count(),
            'vendors': User.objects.filter(role=User.Role.VENDOR).count(),
            'admins': User.objects.filter(role=User.Role.ADMIN).count(),
            'vendor_staff': User.objects.filter(role=User.Role.VENDOR_STAFF).count()
        })