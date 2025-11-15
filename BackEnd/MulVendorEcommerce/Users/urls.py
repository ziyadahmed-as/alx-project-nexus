from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Initialize router
router = DefaultRouter(trailing_slash=False)

# ==================== API Endpoints ====================
router.register('auth', views.AuthViewSet, basename='auth')
router.register('users', views.UserViewSet, basename='user')
router.register('vendor-employees', views.VendorEmployeeViewSet, basename='vendor-employee')
router.register('addresses', views.AddressViewSet, basename='address')

# Profile endpoints
router.register('profiles/customers', views.CustomerProfileViewSet, basename='customer-profile')
router.register('profiles/vendors', views.VendorProfileViewSet, basename='vendor-profile')
router.register('profiles/admins', views.AdminProfileViewSet, basename='admin-profile')

# Admin management
router.register('admin/users', views.AdminUserManagementViewSet, basename='admin-user')

urlpatterns = [
    # API v1 endpoints
    path('api/', include([
        path('', include(router.urls)),
        path('admin/cache/clear', views.CacheManagementView.as_view(), name='cache-clear'),
        path('admin/analytics/users', views.UserAnalyticsView.as_view(), name='user-analytics'),
    ])),
]