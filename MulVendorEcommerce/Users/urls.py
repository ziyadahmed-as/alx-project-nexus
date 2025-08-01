from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from .views import (
    CustomTokenObtainPairView,
    UserRegistrationView,
    UserProfileView,
    CustomerProfileView,
    VendorProfileView,
    VendorVerificationView,
    AdminProfileView,
    VendorEmployeeViewSet,
    AddressViewSet,
    AdminUserManagementViewSet,
    AdminVendorManagementViewSet
)

# Initialize router for ViewSets
router = DefaultRouter()
router.register(r'vendor-employees', VendorEmployeeViewSet, basename='vendor-employee')
router.register(r'addresses', AddressViewSet, basename='address')
router.register(r'admin/users', AdminUserManagementViewSet, basename='admin-user')
router.register(r'admin/vendors', AdminVendorManagementViewSet, basename='admin-vendor')

# Swagger Schema Configuration
schema_view = get_schema_view(
    openapi.Info(
        title="User Management API",
        default_version='v1',
        description="API endpoints for user authentication, registration, and profile management",
        contact=openapi.Contact(email="support@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # ---------------------------
    # Authentication Endpoints
    # ---------------------------
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token-obtain-pair'),
    
    # ---------------------------
    # User Endpoints
    # ---------------------------
    path('register/', UserRegistrationView.as_view(), name='user-registration'),
    path('me/', UserProfileView.as_view(), name='user-profile'),
    
    # ---------------------------
    # Profile Endpoints
    # ---------------------------
    path('me/customer/', CustomerProfileView.as_view(), name='customer-profile'),
    path('me/vendor/', VendorProfileView.as_view(), name='vendor-profile'),
    path('me/admin/', AdminProfileView.as_view(), name='admin-profile'),
    
    # Vendor Verification Endpoint
    path('vendors/<uuid:pk>/verify/', VendorVerificationView.as_view(), name='vendor-verification'),
    
    # ---------------------------
    # Router URLs (ViewSets)
    # ---------------------------
    path('', include(router.urls)),
    
    # ---------------------------
    # API Documentation
    # ---------------------------
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]