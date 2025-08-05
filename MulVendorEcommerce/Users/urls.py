from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AuthViewSet,
    UserViewSet,
    CustomerProfileViewSet,
    VendorProfileViewSet,
    AdminProfileViewSet,
    VendorEmployeeViewSet,
    AddressViewSet,
    AdminUserManagementViewSet,
    AdminVendorManagementViewSet
)

# Create router for ViewSets
router = DefaultRouter()

# Authentication routes
router.register(r'auth', AuthViewSet, basename='auth')

# User management routes
router.register(r'users', UserViewSet, basename='user')

# Profile management routes
router.register(r'profiles/customer', CustomerProfileViewSet, basename='customer-profile')
router.register(r'profiles/vendor', VendorProfileViewSet, basename='vendor-profile')
router.register(r'profiles/admin', AdminProfileViewSet, basename='admin-profile')

# Vendor employee routes
router.register(r'vendor-employees', VendorEmployeeViewSet, basename='vendor-employee')

# Address routes
router.register(r'addresses', AddressViewSet, basename='address')

# Admin management routes
router.register(r'admin/users', AdminUserManagementViewSet, basename='admin-user')
router.register(r'admin/vendors', AdminVendorManagementViewSet, basename='admin-vendor')

urlpatterns = [
    # Include all router URLs
    path('', include(router.urls)),
    
    # Additional custom endpoints
    path('auth/login/', AuthViewSet.as_view({'post': 'login'}), name='auth-login'),
    path('auth/register/', AuthViewSet.as_view({'post': 'register'}), name='auth-register'),
    path('auth/password/reset/', AuthViewSet.as_view({'post': 'password_reset'}), name='auth-password-reset'),
    path('auth/password/reset/confirm/', AuthViewSet.as_view({'post': 'password_reset_confirm'}), name='auth-password-reset-confirm'),
    
    # User-specific endpoints
    path('users/me/', UserViewSet.as_view({'get': 'me', 'patch': 'me'}), name='user-me'),
]

# Optional: Add JWT token endpoints if using SimpleJWT
# from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
# urlpatterns += [
#     path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
#     path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
# ]