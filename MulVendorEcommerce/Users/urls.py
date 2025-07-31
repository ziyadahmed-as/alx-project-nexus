# users/urls.py

from django.urls import path
from .views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    CustomTokenVerifyView,
    UserListCreateAPIView,
    UserRetrieveUpdateDestroyAPIView,
    CustomerListCreateAPIView,
    CustomerRetrieveUpdateDestroyAPIView,
    VendorListCreateAPIView,
    VendorRetrieveUpdateDestroyAPIView,
    AdminProfileListCreateAPIView,
    AdminProfileRetrieveUpdateDestroyAPIView,
    VendorEmployeeListCreateAPIView,
    VendorEmployeeRetrieveUpdateDestroyAPIView,
)
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

# Swagger Schema
schema_view = get_schema_view(
    openapi.Info(
        title="User Management API",
        default_version='v1',
        description="API endpoints for authentication and user profile management (Admin, Vendor, Customer)",
        contact=openapi.Contact(email="support@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Auth
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('auth/verify/', CustomTokenVerifyView.as_view(), name='token_verify'),

    # Users
    path('users/', UserListCreateAPIView.as_view(), name='user-list-create'),
    path('users/<uuid:pk>/', UserRetrieveUpdateDestroyAPIView.as_view(), name='user-detail'),

    # Customers
    path('customers/', CustomerListCreateAPIView.as_view(), name='customer-list-create'),
    path('customers/<uuid:pk>/', CustomerRetrieveUpdateDestroyAPIView.as_view(), name='customer-detail'),

    # Vendors
    path('vendors/', VendorListCreateAPIView.as_view(), name='vendor-list-create'),
    path('vendors/<uuid:pk>/', VendorRetrieveUpdateDestroyAPIView.as_view(), name='vendor-detail'),

    # Admin Profiles
    path('admins/', AdminProfileListCreateAPIView.as_view(), name='admin-list-create'),
    path('admins/<uuid:pk>/', AdminProfileRetrieveUpdateDestroyAPIView.as_view(), name='admin-detail'),

    # Vendor Employees
    path('vendor-employees/', VendorEmployeeListCreateAPIView.as_view(), name='vendor-employee-list-create'),
    path('vendor-employees/<uuid:pk>/', VendorEmployeeRetrieveUpdateDestroyAPIView.as_view(), name='vendor-employee-detail'),

    # Swagger
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
