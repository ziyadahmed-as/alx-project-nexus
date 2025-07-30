from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    # User CRUD
    UserListCreateAPIView,
    UserRetrieveUpdateDestroyAPIView,
    
    # Customer CRUD
    CustomerListCreateAPIView,
    CustomerRetrieveUpdateDestroyAPIView,
    
    # Vendor CRUD
    VendorListCreateAPIView,
    VendorRetrieveUpdateDestroyAPIView,
    
    # Admin Profile CRUD
    AdminProfileListCreateAPIView,
    AdminProfileRetrieveUpdateDestroyAPIView,
    
    # Vendor Employee CRUD
    VendorEmployeeListCreateAPIView,
    VendorEmployeeRetrieveUpdateDestroyAPIView,
    
    # Authentication
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    CustomTokenVerifyView
    
)

urlpatterns = [
    # Authentication
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', CustomTokenVerifyView.as_view(), name='token_verify'),
    # User CRUD
    path('users/', UserListCreateAPIView.as_view(), name='user-list-create'),
    path('users/<uuid:pk>/', UserRetrieveUpdateDestroyAPIView.as_view(), name='user-detail'),
    
    # Customer CRUD
    path('customers/', CustomerListCreateAPIView.as_view(), name='customer-list-create'),
    path('customers/<uuid:pk>/', CustomerRetrieveUpdateDestroyAPIView.as_view(), name='customer-detail'),
    
    # Vendor CRUD
    path('vendors/', VendorListCreateAPIView.as_view(), name='vendor-list-create'),
    path('vendors/<uuid:pk>/', VendorRetrieveUpdateDestroyAPIView.as_view(), name='vendor-detail'),
    
    # Admin Profile CRUD
    path('admin-profiles/', AdminProfileListCreateAPIView.as_view(), name='adminprofile-list-create'),
    path('admin-profiles/<uuid:pk>/', AdminProfileRetrieveUpdateDestroyAPIView.as_view(), name='adminprofile-detail'),
    
    # Vendor Employee CRUD
    path('vendor-employees/', VendorEmployeeListCreateAPIView.as_view(), name='vendoremployee-list-create'),
    path('vendor-employees/<uuid:pk>/', VendorEmployeeRetrieveUpdateDestroyAPIView.as_view(), name='vendoremployee-detail'),
] 