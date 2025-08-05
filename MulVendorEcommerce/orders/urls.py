from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Setup automatic URL routing for all ViewSets
router = DefaultRouter()
router.register('orders', views.OrderViewSet)  # Handles /orders/
router.register('order-items', views.OrderItemViewSet)  # Handles /order-items/
router.register('order-history', views.OrderStatusHistoryViewSet)  # /order-history/
router.register('order-assignments', views.OrderAssignmentHistoryViewSet)  # /order-assignments/
router.register('vendor-dashboards', views.VendorOrderDashboardViewSet)  # /vendor-dashboards/
router.register('order-permissions', views.OrderPermissionViewSet)  # /order-permissions/

# Custom URL patterns
urlpatterns = [
    path('', include(router.urls)),
    
    # Order related custom endpoints
    path('orders/summary/', views.OrderViewSet.as_view({'get': 'summary'})),
    path('orders/export/', views.OrderViewSet.as_view({'get': 'export'})),
    path('orders/recent/', views.OrderViewSet.as_view({'get': 'recent'})),
    path('orders/vendor-dashboard/', views.OrderViewSet.as_view({'get': 'vendor_dashboard'})),
    
    # Single order actions
    path('orders/<int:pk>/update-status/', views.OrderViewSet.as_view({'post': 'update_status'})),
    path('orders/<int:pk>/assign/', views.OrderViewSet.as_view({'post': 'assign'})),
    
    # Cache management
    path('clear-cache/', views.CacheManagementView.as_view()),
]