from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

# Register all ViewSets with the router
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'order-items', views.OrderItemViewSet, basename='orderitem')
router.register(r'order-status-history', views.OrderStatusHistoryViewSet, basename='orderstatushistory')
router.register(r'order-assignment-history', views.OrderAssignmentHistoryViewSet, basename='orderassignmenthistory')
router.register(r'vendor-dashboards', views.VendorOrderDashboardViewSet, basename='vendordashboard')
router.register(r'vendor-analytics', views.VendorOrderAnalyticsViewSet, basename='vendoranalytics')
router.register(r'order-permissions', views.OrderPermissionViewSet, basename='orderpermission')
router.register(r'order-addresses', views.OrderAddressViewSet, basename='orderaddress')  # Changed from 'addresses'

# Additional URL patterns for custom actions and APIViews
urlpatterns = [
    path('', include(router.urls)),
    
    # Cache management endpoint
    path('cache-management/', views.CacheManagementView.as_view(), name='cache-management'),
    
    # Nested routes for order items
    path('orders/<int:order_id>/items/', 
         views.OrderItemViewSet.as_view({
             'get': 'list', 
             'post': 'create'
         }), 
         name='order-items-list'),
    
    # Custom action endpoints for orders
    path('orders/summary/', 
         views.OrderViewSet.as_view({'get': 'summary'}), 
         name='order-summary'),
    path('orders/recent/', 
         views.OrderViewSet.as_view({'get': 'recent'}), 
         name='recent-orders'),
    path('orders/vendor-dashboard/', 
         views.OrderViewSet.as_view({'get': 'vendor_dashboard'}), 
         name='vendor-dashboard'),
    path('orders/<int:pk>/update-status/', 
         views.OrderViewSet.as_view({'post': 'update_status'}), 
         name='order-update-status'),
    path('orders/<int:pk>/assign/', 
         views.OrderViewSet.as_view({'post': 'assign'}), 
         name='order-assign'),
]

# Include DRF auth URLs if needed
urlpatterns += [
    path('api-auth/', include('rest_framework.urls')),
]