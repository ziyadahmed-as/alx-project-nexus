from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from django.shortcuts import get_object_or_404
from .models import User, Customer, Vendor, AdminProfile, VendorEmployee
from .serializers import (
    UserSerializer,
    CustomerSerializer,
    VendorSerializer,
    AdminProfileSerializer,
    VendorEmployeeSerializer,
    CustomTokenObtainPairSerializer
)
from .permissions import IsSuperAdmin, IsVendorOwner, IsProfileOwner

# ====================== AUTHENTICATION ======================
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class CustomTokenRefreshView(TokenRefreshView):
    pass

class CustomTokenVerifyView(TokenVerifyView):
    pass

# ====================== USER CRUD ======================
class UserListCreateAPIView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.AllowAny()]  # Allow registration
        return [IsSuperAdmin()]  # Only superadmin can list users

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class UserRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'pk'

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsSuperAdmin() | IsProfileOwner()]
        return [permissions.IsAuthenticated()]

    def perform_update(self, serializer):
        if 'role' in serializer.validated_data and not self.request.user.is_superuser:
            raise serializers.ValidationError("Only admins can change user roles")
        serializer.save()

# ====================== CUSTOMER CRUD ======================
class CustomerListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = CustomerSerializer

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Customer.objects.all()
        return Customer.objects.filter(user=self.request.user)

    def get_permissions(self):
        if self.request.method == 'POST':
            return []
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        user_data = serializer.validated_data.pop('user')
        user_serializer = UserSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save(role='CUSTOMER')
        serializer.save(user=user)

class CustomerRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsProfileOwner | IsSuperAdmin]

# ====================== VENDOR CRUD ======================
class VendorListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = VendorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Vendor.objects.all()
        return Vendor.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        if self.request.user.role != 'VENDOR':
            self.request.user.role = 'VENDOR'
            self.request.user.save()
        serializer.save(user=self.request.user)

class VendorRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [IsVendorOwner | IsSuperAdmin]

# ====================== ADMIN PROFILE CRUD ======================
class AdminProfileListCreateAPIView(generics.ListCreateAPIView):
    queryset = AdminProfile.objects.all()
    serializer_class = AdminProfileSerializer
    permission_classes = [IsSuperAdmin]

class AdminProfileRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AdminProfile.objects.all()
    serializer_class = AdminProfileSerializer
    permission_classes = [IsSuperAdmin]

# ====================== VENDOR EMPLOYEE CRUD ======================
class VendorEmployeeListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = VendorEmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'VENDOR':
            vendor = get_object_or_404(Vendor, user=self.request.user)
            return VendorEmployee.objects.filter(vendor=vendor)
        return VendorEmployee.objects.all()

    def perform_create(self, serializer):
        if self.request.user.role == 'VENDOR':
            vendor = get_object_or_404(Vendor, user=self.request.user)
            serializer.save(vendor=vendor)
        else:
            serializer.save()

class VendorEmployeeRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = VendorEmployee.objects.all()
    serializer_class = VendorEmployeeSerializer

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsVendorOwner() | IsSuperAdmin()]
        return [permissions.IsAuthenticated()]