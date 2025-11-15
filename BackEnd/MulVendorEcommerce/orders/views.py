from rest_framework import viewsets, permissions, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, Count, Avg, F
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
import redis
from django.conf import settings
from decimal import Decimal

from .models import (
    Order,
    OrderItem,
    OrderStatusHistory,
    OrderAssignmentHistory,
    VendorOrderDashboard,
    VendorOrderAnalytics,
    OrderPermission
)
from .serializers import (
    OrderSerializer,
    OrderItemSerializer,
    OrderStatusHistorySerializer,
    OrderAssignmentHistorySerializer,
    VendorOrderDashboardSerializer,
    VendorOrderAnalyticsSerializer,
    OrderPermissionSerializer,
    OrderAddressSerializer
)
from Users.models import User, Vendor, Address
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

# Cache timeout settings
ORDER_CACHE_TIMEOUT = 60 * 15  # 15 minutes
ORDER_LIST_CACHE_TIMEOUT = 60 * 5  # 5 minutes
ORDER_HISTORY_CACHE_TIMEOUT = 60 * 30  # 30 minutes


class OrderViewSet(viewsets.ModelViewSet):
    """
    Order API endpoint with comprehensive functionality.
    Supports all CRUD operations with role-based access control.
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
        'total': ['gte', 'lte', 'range'],
        'shipping_address': ['exact'],
        'billing_address': ['exact']
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
        """Optimized queryset with role-based filtering and caching"""
        user = self.request.user
        cache_key = f'orders_{user.id}_{hash(frozenset(self.request.query_params.items()))}'
        
        if cached := cache.get(cache_key):
            return cached
            
        queryset = Order.objects.select_related(
            'customer', 'vendor', 'assigned_to', 'last_updated_by',
            'shipping_address', 'billing_address'
        ).prefetch_related(
            'items', 'status_history', 'assignment_history'
        )
        
        queryset = self._apply_role_filters(queryset, user)
        cache.set(cache_key, queryset, ORDER_LIST_CACHE_TIMEOUT)
        return queryset

    def _apply_role_filters(self, queryset, user):
        """Apply role-based filters with optimized queries"""
        if user.is_superuser:
            return queryset
        
        if hasattr(user, 'customer_profile'):
            return queryset.filter(customer=user)
            
        if hasattr(user, 'vendor'):
            return queryset.filter(vendor=user.vendor)
            
        if hasattr(user, 'vendor_employee'):
            vendor = user.vendor_employee.vendor
            base_query = queryset.filter(vendor=vendor)
            
            # Check if employee has permission to view all orders
            if not user.vendor_employee.can_view_all_orders:
                return base_query.filter(Q(assigned_to=user) | Q(assigned_to__isnull=True))
            return base_query
            
        return queryset.none()

    def get_permissions(self):
        """Dynamic permission assignment based on action"""
        if self.action == 'create':
            return [permissions.IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [(IsVendorOwner | IsSuperAdmin)()]
        elif self.action in ['assign', 'update_status']:
            return [(IsVendorOwner | IsVendorEmployee | IsSuperAdmin)()]
        return [permissions.IsAuthenticated()]

    def retrieve(self, request, *args, **kwargs):
        """Optimized single order retrieval with caching"""
        cache_key = f'order_{kwargs["pk"]}_{request.user.id}'
        if cached := cache.get(cache_key):
            return Response(cached)
            
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        cache.set(cache_key, serializer.data, ORDER_CACHE_TIMEOUT)
        return Response(serializer.data)

    @transaction.atomic
    def perform_create(self, serializer):
        """Atomic order creation with validation"""
        user = self.request.user
        if not hasattr(user, 'customer_profile'):
            raise PermissionDenied("Only customers can create orders")
            
        # Validate addresses belong to customer
        shipping_address = serializer.validated_data.get('shipping_address')
        billing_address = serializer.validated_data.get('billing_address')
        
        if shipping_address and shipping_address.user != user:
            raise ValidationError("Shipping address must belong to the customer")
        if billing_address and billing_address.user != user:
            raise ValidationError("Billing address must belong to the customer")
            
        serializer.save(
            customer=user,
            status=Order.Status.PENDING_PAYMENT,  # Updated to match new status
            last_updated_by=user
        )

    @transaction.atomic
    def perform_update(self, serializer):
        """Track updates atomically with validation"""
        user = self.request.user
        instance = self.get_object()
        
        # For vendors/employees, validate they can't change customer addresses
        if hasattr(user, 'vendor') or hasattr(user, 'vendor_employee'):
            if 'shipping_address' in serializer.validated_data or 'billing_address' in serializer.validated_data:
                raise PermissionDenied("Cannot modify customer addresses")
            
            # Validate notes permissions
            if 'admin_notes' in serializer.validated_data:
                if hasattr(user, 'vendor_employee') and not user.vendor_employee.can_edit_order_items:
                    raise PermissionDenied("Cannot modify admin notes")
        
        serializer.save(last_updated_by=user)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Status update endpoint with validation"""
        order = self.get_object()
        new_status = request.data.get('status')
        note = request.data.get('note', '')
        
        if not new_status:
            raise ValidationError("Status is required")
            
        if new_status not in dict(Order.Status.choices):
            raise ValidationError("Invalid status")
            
        # Check if user has permission to make this status change
        if new_status not in order.get_status_actions(request.user):
            raise PermissionDenied("Invalid status transition")
            
        with transaction.atomic():
            # Record status history
            OrderStatusHistory.objects.create(
                order=order,
                old_status=order.status,
                new_status=new_status,
                changed_by=request.user,
                note=note
            )
            
            # Update order
            order.status = new_status
            order.status_changed_at = timezone.now()
            order.last_updated_by = request.user
            order.save()
            
            # Clear relevant caches
            cache.delete_pattern(f'order_{order.id}_*')
            cache.delete_pattern(f'orders_*')
            
        return Response(self.get_serializer(order).data)

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Order assignment with validation"""
        order = self.get_object()
        assigned_to_id = request.data.get('assigned_to_id')
        
        if not assigned_to_id:
            raise ValidationError("assigned_to_id is required")
            
        try:
            assigned_to = User.objects.get(pk=assigned_to_id)
        except User.DoesNotExist:
            raise ValidationError("User not found")
            
        # Check if user has permission to assign
        if not (request.user.is_superuser or 
               (hasattr(request.user, 'vendor') and order.vendor == request.user.vendor) or
               (hasattr(request.user, 'vendor_employee') and 
                order.vendor == request.user.vendor_employee.vendor and
                request.user.vendor_employee.can_assign_orders)):
            raise PermissionDenied("You don't have permission to assign orders")
            
        with transaction.atomic():
            # End current assignment if exists
            OrderAssignmentHistory.objects.filter(
                order=order,
                active=True
            ).update(
                active=False,
                ended_at=timezone.now()
            )
            
            # Create new assignment
            OrderAssignmentHistory.objects.create(
                order=order,
                assigned_to=assigned_to,
                assigned_by=request.user,
                active=True
            )
            
            # Update order
            order.assigned_to = assigned_to
            order.last_updated_by = request.user
            order.save()
            
            # Clear relevant caches
            cache.delete_pattern(f'order_{order.id}_*')
            cache.delete_pattern(f'orders_*')
            
        return Response(self.get_serializer(order).data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Order summary with caching"""
        cache_key = f'order_summary_{request.user.id}_{hash(frozenset(request.query_params.items()))}'
        if cached := cache.get(cache_key):
            return Response(cached)
            
        queryset = self.filter_queryset(self.get_queryset())
        
        summary = {
            'total_orders': queryset.count(),
            'total_revenue': queryset.aggregate(total=Sum('total'))['total'] or 0,
            'status_counts': queryset.values('status').annotate(
                count=Count('id'),
                revenue=Sum('total')
            ),
            'avg_order_value': queryset.aggregate(avg=Avg('total'))['avg'] or 0
        }
        
        cache.set(cache_key, summary, ORDER_CACHE_TIMEOUT)
        return Response(summary)

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Recent orders endpoint"""
        cache_key = f'recent_orders_{request.user.id}'
        if cached := cache.get(cache_key):
            return Response(cached)
            
        queryset = self.filter_queryset(self.get_queryset()).filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).order_by('-created_at')[:10]
        
        serializer = self.get_serializer(queryset, many=True)
        cache.set(cache_key, serializer.data, ORDER_CACHE_TIMEOUT)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsVendorOwner | IsVendorEmployee])
    def vendor_dashboard(self, request):
        """Vendor dashboard with comprehensive metrics"""
        vendor = getattr(request.user, 'vendor', 
                       getattr(request.user.vendor_employee, 'vendor', None))
        cache_key = f'vendor_dashboard_{vendor.id}'
        if cached := cache.get(cache_key):
            return Response(cached)
            
        # Get vendor analytics
        analytics, _ = VendorOrderAnalytics.objects.get_or_create(vendor=vendor)
        analytics_serializer = VendorOrderAnalyticsSerializer(analytics)
        
        # Get dashboard settings
        dashboard, _ = VendorOrderDashboard.objects.get_or_create(vendor=vendor)
        dashboard_serializer = VendorOrderDashboardSerializer(dashboard)
        
        response_data = {
            'analytics': analytics_serializer.data,
            'dashboard': dashboard_serializer.data,
            'recent_orders': self._get_recent_vendor_orders(vendor)
        }
        
        cache.set(cache_key, response_data, ORDER_CACHE_TIMEOUT)
        return Response(response_data)

    def _get_recent_vendor_orders(self, vendor, limit=5):
        """Get recent orders for vendor dashboard"""
        orders = Order.objects.filter(
            vendor=vendor
        ).select_related('customer', 'assigned_to'
        ).order_by('-created_at')[:limit]
        
        return OrderSerializer(orders, many=True).data


class OrderItemViewSet(viewsets.ModelViewSet):
    """OrderItem API endpoint with role-based access control"""
    serializer_class = OrderItemSerializer
    queryset = OrderItem.objects.select_related(
        'order', 'product', 'variant'
    )
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['order', 'product', 'variant']

    def get_permissions(self):
        """Dynamic permission assignment"""
        if self.action == 'create':
            return [permissions.IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [(IsVendorOwner | IsSuperAdmin)()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        """Role-based queryset filtering"""
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

    def get_serializer_context(self):
        """Add order to serializer context"""
        context = super().get_serializer_context()
        if 'order_id' in self.kwargs:
            context['order'] = Order.objects.get(pk=self.kwargs['order_id'])
        return context

    @transaction.atomic
    def perform_create(self, serializer):
        """Validate and create order item with permission checks"""
        order = serializer.validated_data['order']
        user = self.request.user
        
        if hasattr(user, 'customer_profile'):
            if order.customer != user or order.status != Order.Status.PENDING_PAYMENT:  # Updated status
                raise PermissionDenied("Can only add to your pending orders")
        elif hasattr(user, 'vendor'):
            if order.vendor != user.vendor:
                raise PermissionDenied("Can only add to your vendor's orders")
        elif hasattr(user, 'vendor_employee'):
            if order.vendor != user.vendor_employee.vendor or not user.vendor_employee.can_edit_order_items:
                raise PermissionDenied("No permission to add items")
        
        serializer.save()


class OrderStatusHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only API for Order Status History"""
    serializer_class = OrderStatusHistorySerializer
    queryset = OrderStatusHistory.objects.select_related(
        'order', 'changed_by'
    )
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['order', 'changed_by', 'new_status']

    def get_queryset(self):
        """Role-based queryset filtering"""
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
    """Read-only API for Order Assignment History"""
    serializer_class = OrderAssignmentHistorySerializer
    queryset = OrderAssignmentHistory.objects.select_related(
        'order', 'assigned_to', 'assigned_by'
    )
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['order', 'assigned_to', 'assigned_by', 'active']

    def get_queryset(self):
        """Role-based queryset filtering"""
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
    """API for Vendor Dashboard Configuration"""
    serializer_class = VendorOrderDashboardSerializer
    queryset = VendorOrderDashboard.objects.select_related('vendor')
    permission_classes = [IsVendorOwner | IsSuperAdmin]

    def get_queryset(self):
        """Restrict to vendor's own dashboard"""
        user = self.request.user
        if user.is_superuser:
            return super().get_queryset()
        return super().get_queryset().filter(vendor=user.vendor)

    @transaction.atomic
    def perform_create(self, serializer):
        """Auto-associate dashboard with vendor"""
        if not hasattr(self.request.user, 'vendor'):
            raise PermissionDenied("Only vendors can create dashboards")
        serializer.save(vendor=self.request.user.vendor)


class VendorOrderAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only API for Vendor Order Analytics"""
    serializer_class = VendorOrderAnalyticsSerializer
    queryset = VendorOrderAnalytics.objects.select_related('vendor')
    permission_classes = [IsVendorOwner | IsSuperAdmin]

    def get_queryset(self):
        """Restrict to vendor's own analytics"""
        user = self.request.user
        if user.is_superuser:
            return super().get_queryset()
        return super().get_queryset().filter(vendor=user.vendor)


class OrderPermissionViewSet(viewsets.ModelViewSet):
    """API for Managing Order Permissions"""
    serializer_class = OrderPermissionSerializer
    queryset = OrderPermission.objects.all()
    permission_classes = [IsSuperAdmin]


class OrderAddressViewSet(viewsets.ModelViewSet):
    """API for Address management specific to Orders"""
    serializer_class = OrderAddressSerializer
    queryset = Address.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Users can only see their own addresses"""
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Auto-associate address with user"""
        serializer.save(user=self.request.user)


class CacheManagementView(APIView):
    """API for Cache Management Operations"""
    permission_classes = [IsSuperAdmin]

    def post(self, request):
        """Clear specified cache segments"""
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