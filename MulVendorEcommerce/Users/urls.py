from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'vendor-employees', views.VendorEmployeeViewSet, basename='vendor-employee')
router.register(r'addresses', views.AddressViewSet, basename='address')
router.register(r'admin/users', views.AdminUserManagementViewSet, basename='admin-user')
router.register(r'admin/vendors', views.AdminVendorManagementViewSet, basename='admin-vendor')

urlpatterns = [
    # Authentication
    path('auth/login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    # Registration
    path('register/customer/', views.UserRegistrationView.as_view(), name='register-customer'),
    path('register/vendor/', views.UserRegistrationView.as_view(), name='register-vendor'),
    path('register/vendor-employee/', views.UserRegistrationView.as_view(), name='register-vendor-employee'),
    
    # User Profiles
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('profile/customer/', views.CustomerProfileView.as_view(), name='customer-profile'),
    path('profile/vendor/', views.VendorView.as_view(), name='vendor-profile'),
    path('profile/vendor/business/', views.VendorProfileView.as_view(), name='vendor-business-profile'),
    path('profile/admin/', views.AdminProfileView.as_view(), name='admin-profile'),
    
    # Vendor Verification
    path('vendors/<uuid:pk>/verify/', views.VendorVerificationView.as_view(), name='vendor-verify'),
    
    # Include router URLs
    path('', include(router.urls)),
]