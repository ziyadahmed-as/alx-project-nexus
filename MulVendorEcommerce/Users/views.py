from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.exceptions import PermissionDenied

from .models import Customer, Vendor, AdminProfile, VendorEmployee, Address
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserDetailSerializer,
    CustomerProfileSerializer,
    VendorProfileSerializer,
    AdminProfileSerializer,
    VendorEmployeeProfileSerializer,
    AddressSerializer,
    AdminUserManagementSerializer,
    AdminVendorManagementSerializer,
    CustomerRegistrationSerializer,
    VendorRegistrationSerializer
)
# this line is necessary to ensure the User model is loaded
User = get_user_model()

# Custom Token Obtain Pair View to use our custom serializer
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

# this view handles user registration for both customers and vendors
class UserRegistrationView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        role = self.request.data.get('role', User.Role.CUSTOMER)
        if role == User.Role.CUSTOMER:
            return CustomerRegistrationSerializer
        elif role == User.Role.VENDOR:
            return VendorRegistrationSerializer
        return super().get_serializer_class()

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        role = request.data.get('role', User.Role.CUSTOMER)
        
        if role not in [User.Role.CUSTOMER, User.Role.VENDOR]:
            return Response(
                {"detail": "Invalid registration role. Must be either 'CUSTOMER' or 'VENDOR'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            instance = serializer.save()
            response_serializer = (
                CustomerProfileSerializer(instance) if role == User.Role.CUSTOMER
                else VendorProfileSerializer(instance)
            )
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
        return self.request.user


class CustomerProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = CustomerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        if self.request.user.role != User.Role.CUSTOMER:
            raise PermissionDenied("You are not a customer")
        return get_object_or_404(Customer.objects.select_related('user'), user=self.request.user)


class VendorProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = VendorProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        if self.request.user.role != User.Role.VENDOR:
            raise PermissionDenied("You are not a vendor")
        return get_object_or_404(Vendor.objects.select_related('user'), user=self.request.user)


class VendorVerificationView(generics.UpdateAPIView):
    queryset = Vendor.objects.select_related('user', 'verified_by')
    serializer_class = AdminVendorManagementSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = 'pk'

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        vendor = self.get_object()
        new_status = request.data.get('verification_status')
        
        if new_status not in [Vendor.VerificationStatus.VERIFIED, Vendor.VerificationStatus.REJECTED]:
            return Response(
                {"detail": "Invalid verification status. Must be either 'verified' or 'rejected'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            vendor.verification_status = new_status
            vendor.verification_notes = request.data.get('verification_notes', '')
            vendor.verified_by = request.user
            vendor.verified_at = timezone.now()
            vendor.save()

            serializer = self.get_serializer(vendor)
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
        return get_object_or_404(AdminProfile.objects.select_related('user'), user=self.request.user)


class VendorEmployeeViewSet(viewsets.ModelViewSet):
    serializer_class = VendorEmployeeProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        if self.request.user.role == User.Role.VENDOR:
            vendor = get_object_or_404(Vendor, user=self.request.user)
            return VendorEmployee.objects.filter(vendor=vendor).select_related('user', 'vendor')
        return VendorEmployee.objects.none()

    def perform_create(self, serializer):
        if self.request.user.role != User.Role.VENDOR:
            raise PermissionDenied("Only vendors can create employees")
        vendor = get_object_or_404(Vendor, user=self.request.user)
        serializer.save(vendor=vendor)


class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user).select_related('user')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AdminUserManagementViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = AdminUserManagementSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['role', 'is_active', 'is_verified']
    search_fields = ['email', 'username']
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return super().get_queryset().select_related('customer', 'vendor', 'adminprofile')

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        user = self.get_object()
        if user.is_active:
            return Response(
                {'status': 'User is already active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.is_active = True
        user.save()
        return Response(
            {'status': 'User activated successfully'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        user = self.get_object()
        if not user.is_active:
            return Response(
                {'status': 'User is already inactive'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.is_active = False
        user.save()
        return Response(
            {'status': 'User deactivated successfully'},
            status=status.HTTP_200_OK
        )


class AdminVendorManagementViewSet(viewsets.ModelViewSet):
    queryset = Vendor.objects.all().order_by('-created_at').select_related('user', 'verified_by')
    serializer_class = AdminVendorManagementSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['verification_status', 'is_active']
    search_fields = ['business_name', 'user__email']
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        vendor = self.get_object()
        if vendor.verification_status == Vendor.VerificationStatus.VERIFIED:
            return Response(
                {'status': 'Vendor is already verified'},
                status=status.HTTP_400_BAD_REQUEST
            )
        vendor.verification_status = Vendor.VerificationStatus.VERIFIED
        vendor.verified_by = request.user
        vendor.verified_at = timezone.now()
        vendor.save()
        return Response(
            {'status': 'Vendor verified successfully'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        vendor = self.get_object()
        if vendor.verification_status == Vendor.VerificationStatus.REJECTED:
            return Response(
                {'status': 'Vendor is already rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )
        vendor.verification_status = Vendor.VerificationStatus.REJECTED
        vendor.verification_notes = request.data.get('notes', '')
        vendor.verified_by = request.user
        vendor.verified_at = timezone.now()
        vendor.save()
        return Response(
            {'status': 'Vendor rejected successfully'},
            status=status.HTTP_200_OK
        )