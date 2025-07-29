from rest_framework import generics, status, mixins
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import User, Customer, Vendor, AdminProfile, VendorEmployee
from .serializers import (
    UserSerializer,
    CustomerSerializer,
    VendorSerializer,
    AdminProfileSerializer,
    VendorEmployeeSerializer
)
from .permissions import IsSuperAdmin, IsVendorOwner, IsProfileOwner

# ====================== USER CRUD ======================
# This view handles listing and creating users.
# It is restricted to super admins only.
class UserListCreateAPIView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsSuperAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

# It allows retrieval, updating, and deletion of user profiles.
class UserRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsSuperAdmin | IsProfileOwner]

    def perform_update(self, serializer):
        if 'role' in serializer.validated_data and not self.request.user.is_superuser:
            raise serializers.ValidationError("Only admins can change user roles")
        serializer.save()

# ====================== CUSTOMER CRUD ======================
# This view handles listing and creating customers.
# It allows anyone to register as a customer, but only authenticated users can access the list.
class CustomerListCreateAPIView(generics.ListCreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return []  # Allow anyone to register as customer
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        user_data = serializer.validated_data.pop('user')
        user = User.objects.create_user(**user_data, role='CUSTOMER')
        serializer.save(user=user)

class CustomerRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsProfileOwner | IsSuperAdmin]

# ====================== VENDOR CRUD ======================
# This view handles listing and creating vendors.
# It is restricted to authenticated users, and only vendors can create vendor profiles.
class VendorListCreateAPIView(generics.ListCreateAPIView):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        if self.request.user.role != 'VENDOR':
            serializer.save(user=self.request.user)
            self.request.user.role = 'VENDOR'
            self.request.user.save()
            
# If the user is a vendor, associate the vendor with the user.
class VendorRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [IsVendorOwner | IsSuperAdmin]

# ====================== ADMIN PROFILE CRUD ======================
# This view handles listing and creating admin profiles.
# It is restricted to super admins only.
class AdminProfileListCreateAPIView(generics.ListCreateAPIView):
    queryset = AdminProfile.objects.all()
    serializer_class = AdminProfileSerializer
    permission_classes = [IsSuperAdmin]

# It allows retrieval, updating, and deletion of admin profiles.
class AdminProfileRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AdminProfile.objects.all()
    serializer_class = AdminProfileSerializer
    permission_classes = [IsSuperAdmin]

# ====================== VENDOR EMPLOYEE CRUD ======================
# This view handles listing and creating vendor employees.
# It is restricted to authenticated users, and only vendors can create vendor employees.
class VendorEmployeeListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = VendorEmployeeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'VENDOR':
            return VendorEmployee.objects.filter(vendor__user=self.request.user)
        return VendorEmployee.objects.all()

    def perform_create(self, serializer):
        if self.request.user.role == 'VENDOR':
            vendor = get_object_or_404(Vendor, user=self.request.user)
            serializer.save(vendor=vendor)
        else:
            serializer.save()
# It allows retrieval, updating, and deletion of vendor employees.  
class VendorEmployeeRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = VendorEmployee.objects.all()
    serializer_class = VendorEmployeeSerializer

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsVendorOwner | IsSuperAdmin]
        return [IsAuthenticated()]