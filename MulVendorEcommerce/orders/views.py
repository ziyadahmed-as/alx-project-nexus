from rest_framework import viewsets, permissions, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied,  ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, Count
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import redis
from django.conf import settings

from .models import (
    Order,
    OrderItem,
    OrderStatusHistory,
    OrderAssignmentHistory,
    VendorOrderDashboard,
    OrderPermission
)
from .serializers import (
    OrderSerializer,
    OrderItemSerializer,
    OrderStatusHistorySerializer,
    OrderAssignmentHistorySerializer,
    VendorOrderDashboardSerializer,
    OrderPermissionSerializer,
    OrderStatusUpdateSerializer,
    OrderAssignmentSerializer,
    OrderSummarySerializer,
    OrderExportSerializer
)
from Users.models import User, Vendor, VendorEmployee
from Users.permissions import (
    IsVendorOwner,
    IsVendorEmployee,
    IsSuperAdmin,
    IsProfileOwner
)

# Initialize Redis connection
redis_client = redis.StrictRedis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
)

# Cache timeout settings (in seconds)
ORDER_CACHE_TIMEOUT = 60 * 15  # 15 minutes
ORDER_LIST_CACHE_TIMEOUT = 60 * 5  # 5 minutes
ORDER_HISTORY_CACHE_TIMEOUT = 60 * 30  # 30 minutes


class OrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint for order management with multi-role support.
    
    Provides comprehensive order operations including:
    - CRUD operations with role-based permissions
    - Status transitions with validation
    - Order assignment to employees
    - Customer, vendor, and admin views
    - Advanced filtering and search
    - Caching for performance
    """
    
    serializer_class = OrderSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'status': ['exact', 'in'],
        'vendor': ['exact'],
        'customer': ['exact'],
        'assigned_to': ['exact', 'isnull'],
        'payment_method': ['exact'],
        'created_at': ['date', 'gte', 'lte', 'range'],
        'total': ['gte', 'lte', 'range']
    }
    search_fields = [
        'order_number',
        'customer__email',
        'customer__first_name',
        'customer__last_name',
        'vendor__user__business_name'
    ]
    ordering_fields = [
        'created_at',
        'updated_at',
        'total',
        'status_changed_at'
    ]
    ordering = ['-created_at']

    def get_queryset(self):
        """Retrieve orders with role-based filtering and caching"""
        user = self.request.user
        cache_key = self._generate_cache_key(user)
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return cached_data
            
        queryset = Order.objects.select_related(
            'customer', 'vendor', 'vendor__user',
            'assigned_to', 'last_updated_by'
        ).prefetch_related(
            'items', 'status_history', 'assignment_history'
        )
        
        queryset = self._apply_role_filters(queryset, user)
        cache.set(cache_key, queryset, timeout=ORDER_LIST_CACHE_TIMEOUT)
        return queryset

    def _generate_cache_key(self, user):
        """Generate dynamic cache key based on user and request params"""
        base_key = 'orders_'
        params = self.request.query_params.dict()
        
        if user.is_superuser:
            base_key += 'admin_'
        elif hasattr(user, 'customer_profile'):
            base_key += f'customer_{user.id}_'
        elif hasattr(user, 'vendor'):
            base_key += f'vendor_{user.vendor.id}_'
        elif hasattr(user, 'vendor_employee'):
            base_key += f'vendor_employee_{user.id}_'
        else:
            base_key += 'public_'
            
        return base_key + '_'.join(f"{k}_{v}" for k, v in sorted(params.items()))

    def _apply_role_filters(self, queryset, user):
        """Apply role-specific filters to the queryset"""
        if user.is_superuser:
            return queryset
        
        if hasattr(user, 'customer_profile'):
            return queryset.filter(customer=user)
            
        if hasattr(user, 'vendor'):
            return queryset.filter(vendor=user.vendor)
            
        if hasattr(user, 'vendor_employee'):
            # Employees can see assigned orders or all vendor orders based on permissions
            if user.vendor_employee.can_view_all_orders:
                return queryset.filter(vendor=user.vendor_employee.vendor)
            return queryset.filter(
                Q(vendor=user.vendor_employee.vendor) &
                (Q(assigned_to=user) | Q(assigned_to__isnull=True)))
                
        return queryset.none()  # Anonymous users see no orders

    def get_permissions(self):
        """Dynamically assign permissions based on action"""
        if self.action == 'create':
            return [permissions.IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [(IsVendorOwner | IsSuperAdmin)()]
        elif self.action in ['assign', 'update_status']:
            return [(IsVendorOwner | IsVendorEmployee | IsSuperAdmin)()]
        return [permissions.IsAuthenticatedOrReadOnly()]

    def retrieve(self, request, *args, **kwargs):
        """Retrieve single order with caching"""
        cache_key = f'order_{kwargs["pk"]}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
            
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        response = Response(serializer.data)
        cache.set(cache_key, serializer.data, timeout=ORDER_CACHE_TIMEOUT)
        return response

    def perform_create(self, serializer):
        """Set order creator and initial status"""
        user = self.request.user
        if hasattr(user, 'customer_profile'):
            serializer.save(
                customer=user,
                status=Order.Status.DRAFT,
                last_updated_by=user
            )
        else:
            raise PermissionDenied("Only customers can create orders")

    def perform_update(self, serializer):
        """Track who made the update"""
        serializer.save(last_updated_by=self.request.user)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """
        Update order status with validation
        
        Parameters:
        - new_status: The new status (required)
        - note: Optional note about the status change
        
        Returns:
        The updated order
        """
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(
            data=request.data,
            context={'order': order, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.update(order, serializer.validated_data)
        return Response(self.get_serializer(order).data)

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """
        Assign order to a vendor employee
        
        Parameters:
        - employee_id: ID of the employee to assign (required)
        
        Returns:
        The updated order
        """
        order = self.get_object()
        serializer = OrderAssignmentSerializer(
            data=request.data,
            context={'order': order, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.update(order, serializer.validated_data)
        return Response(self.get_serializer(order).data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get order summary statistics by status
        
        Returns:
        List of status counts with totals
        """
        user = request.user
        cache_key = f'order_summary_{user.id if user.is_authenticated else "anon"}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
            
        queryset = self.filter_queryset(self.get_queryset())
        
        # Get counts and totals by status
        summary = queryset.values('status').annotate(
            count=Count('id'),
            total_amount=Sum('total')
        ).order_by('status')
        
        serializer = OrderSummarySerializer(summary, many=True)
        response_data = serializer.data
        cache.set(cache_key, response_data, timeout=ORDER_CACHE_TIMEOUT)
        return Response(response_data)

    @action(detail=False, methods=['get'])
    def export(self, request):
        """
        Export orders as CSV or Excel
        
        Parameters:
        - format: csv or xlsx (default: csv)
        
        Returns:
        File download of exported orders
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = OrderExportSerializer(queryset, many=True)
        
        format = request.query_params.get('format', 'csv').lower()
        if format not in ['csv', 'xlsx']:
            format = 'csv'
            
        # Generate file response (implementation depends on your export library)
        # Example using django-rest-framework-csv:
        # response = CSVResponse(serializer.data)
        # response['Content-Disposition'] = f'attachment; filename="orders_export.{format}"'
        # return response
        
        return Response(serializer.data)  # Fallback to JSON if export not configured

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        Get recent orders for the current user's role
        
        Returns:
        List of recent orders (last 30 days)
        """
        user = request.user
        cache_key = f'recent_orders_{user.id if user.is_authenticated else "anon"}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
            
        queryset = self.filter_queryset(self.get_queryset()).filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).order_by('-created_at')[:20]
        
        serializer = self.get_serializer(queryset, many=True)
        response_data = serializer.data
        cache.set(cache_key, response_data, timeout=ORDER_CACHE_TIMEOUT)
        return Response(response_data)

    @action(detail=False, methods=['get'], permission_classes=[IsVendorOwner | IsVendorEmployee])
    def vendor_dashboard(self, request):
        """
        Get vendor-specific order dashboard data
        
        Returns:
        - Counts by status
        - Recent activity
        - Performance metrics
        """
        user = request.user
        vendor = user.vendor if hasattr(user, 'vendor') else user.vendor_employee.vendor
        cache_key = f'vendor_dashboard_{vendor.id}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
            
        # Status counts
        status_counts = Order.objects.filter(vendor=vendor).values(
            'status'
        ).annotate(
            count=Count('id')
        ).order_by('status')
        
        # Recent orders
        recent_orders = Order.objects.filter(
            vendor=vendor
        ).order_by('-created_at')[:5]
        
        # Performance metrics
        metrics = {
            'avg_processing_time': None,  # Would calculate actual metrics
            'completion_rate': None,
            'revenue_30d': None
        }
        
        response_data = {
            'status_counts': status_counts,
            'recent_orders': OrderSerializer(recent_orders, many=True).data,
            'metrics': metrics
        }
        
        cache.set(cache_key, response_data, timeout=ORDER_CACHE_TIMEOUT)
        return Response(response_data)


class OrderItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint for order item management.
    
    Provides CRUD operations for order items with role-based permissions.
    """
    
    serializer_class = OrderItemSerializer
    queryset = OrderItem.objects.select_related(
        'order', 'product', 'variant'
    )

    def get_permissions(self):
        """Dynamically assign permissions based on action"""
        if self.action == 'create':
            return [permissions.IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [(IsVendorOwner | IsSuperAdmin)()]
        return [permissions.IsAuthenticatedOrReadOnly()]

    def get_queryset(self):
        """Apply role-based filtering"""
        user = self.request.user
        queryset = super().get_queryset()
        
        if user.is_superuser:
            return queryset
            
        if hasattr(user, 'customer_profile'):
            return queryset.filter(order__customer=user)
            
        if hasattr(user, 'vendor') or hasattr(user, 'vendor_employee'):
            vendor = user.vendor if hasattr(user, 'vendor') else user.vendor_employee.vendor
            return queryset.filter(order__vendor=vendor)
            
        return queryset.none()

    def perform_create(self, serializer):
        """Validate order belongs to requesting vendor"""
        order = serializer.validated_data['order']
        user = self.request.user
        
        # Customers can only add to their own draft orders
        if hasattr(user, 'customer_profile'):
            if order.customer != user or order.status != Order.Status.DRAFT:
                raise PermissionDenied("Can only add items to your own draft orders")
        
        # Vendors can only add to their own orders
        elif hasattr(user, 'vendor'):
            if order.vendor != user.vendor:
                raise PermissionDenied("Can only add items to your vendor's orders")
        
        # Vendor employees need specific permission
        elif hasattr(user, 'vendor_employee'):
            if order.vendor != user.vendor_employee.vendor or not user.vendor_employee.can_edit_order_items:
                raise PermissionDenied("You don't have permission to add items to orders")
        
        serializer.save()


class OrderStatusHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for order status history.
    
    Provides read-only access to order status change history.
    """
    
    serializer_class = OrderStatusHistorySerializer
    queryset = OrderStatusHistory.objects.select_related(
        'order', 'changed_by'
    ).order_by('-created_at')
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['order', 'changed_by', 'new_status']

    def get_queryset(self):
        """Apply role-based filtering"""
        user = self.request.user
        queryset = super().get_queryset()
        
        if user.is_superuser:
            return queryset
            
        if hasattr(user, 'customer_profile'):
            return queryset.filter(order__customer=user)
            
        if hasattr(user, 'vendor') or hasattr(user, 'vendor_employee'):
            vendor = user.vendor if hasattr(user, 'vendor') else user.vendor_employee.vendor
            return queryset.filter(order__vendor=vendor)
            
        return queryset.none()


class OrderAssignmentHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for order assignment history.
    
    Provides read-only access to order assignment history.
    """
    
    serializer_class = OrderAssignmentHistorySerializer
    queryset = OrderAssignmentHistory.objects.select_related(
        'order', 'assigned_to', 'assigned_by'
    ).order_by('-created_at')
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['order', 'assigned_to', 'assigned_by', 'active']

    def get_queryset(self):
        """Apply role-based filtering"""
        user = self.request.user
        queryset = super().get_queryset()
        
        if user.is_superuser:
            return queryset
            
        if hasattr(user, 'customer_profile'):
            return queryset.filter(order__customer=user)
            
        if hasattr(user, 'vendor') or hasattr(user, 'vendor_employee'):
            vendor = user.vendor if hasattr(user, 'vendor') else user.vendor_employee.vendor
            return queryset.filter(order__vendor=vendor)
            
        return queryset.none()


class VendorOrderDashboardViewSet(viewsets.ModelViewSet):
    """
    API endpoint for vendor order dashboard configurations.
    
    Allows vendors to customize their order dashboard display.
    """
    
    serializer_class = VendorOrderDashboardSerializer
    queryset = VendorOrderDashboard.objects.select_related('vendor')
    permission_classes = [IsVendorOwner | IsSuperAdmin]

    def get_queryset(self):
        """Restrict to vendor's own dashboard"""
        user = self.request.user
        if user.is_superuser:
            return super().get_queryset()
        return super().get_queryset().filter(vendor=user.vendor)

    def perform_create(self, serializer):
        """Auto-associate with vendor"""
        if hasattr(self.request.user, 'vendor'):
            serializer.save(vendor=self.request.user.vendor)
        else:
            raise PermissionDenied("Only vendors can create dashboards")


class OrderPermissionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for order permissions management.
    
    Allows admins to configure role-based order permissions.
    """
    
    serializer_class = OrderPermissionSerializer
    queryset = OrderPermission.objects.all()
    permission_classes = [IsSuperAdmin]


class CacheManagementView(APIView):
    """
    API endpoint for managing order-related cache.
    
    Provides operations to clear specific cache segments.
    Restricted to superadmins only.
    """
    
    permission_classes = [IsSuperAdmin]

    def post(self, request):
        """
        Clear order-related cache segments
        
        Parameters:
        - segment: Cache segment to clear (orders, items, history)
        
        Returns:
        Status message
        """
        segment = request.data.get('segment')
        
        if segment == 'orders':
            cache.delete_pattern('order_*')
            cache.delete_pattern('orders_*')
            return Response({'status': 'Order cache cleared'})
        
        elif segment == 'items':
            cache.delete_pattern('order_item_*')
            return Response({'status': 'Order items cache cleared'})
        
        elif segment == 'history':
            cache.delete_pattern('order_history_*')
            return Response({'status': 'Order history cache cleared'})
        
        return Response(
            {'error': 'Invalid segment specified'},
            status=status.HTTP_400_BAD_REQUEST
        )
        
   