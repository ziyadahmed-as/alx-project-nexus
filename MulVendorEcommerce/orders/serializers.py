from rest_framework import serializers
from .models import (
    Order, 
    OrderItem, 
    OrderStatusHistory,
    OrderAssignmentHistory,
    VendorOrderDashboard,
    OrderPermission
)
from Users.models import User, Vendor
from products.models import Product, ProductVariant
from Users.serializers import UserSerializer, VendorProfileSerializer
from products.serializers import ProductSerializer, ProductVariantSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for OrderItem model with role-based field visibility"""
    product = ProductSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(),
        source='variant',
        write_only=True,
        allow_null=True
    )

    class Meta:
        model = OrderItem
        fields = [
            'id', 'order', 'product', 'product_id', 'variant', 'variant_id',
            'quantity', 'price', 'tax_amount', 'discount_amount', 'total',
            'vendor_notes', 'admin_notes'
        ]
        read_only_fields = ['total']
        extra_kwargs = {
            'vendor_notes': {'required': False},
            'admin_notes': {'required': False}
        }

    def get_fields(self):
        """Dynamically modify fields based on user role"""
        fields = super().get_fields()
        request = self.context.get('request', None)
        
        if request and hasattr(request, 'user'):
            user = request.user
            
            # Hide admin notes from non-admin users
            if not (user.is_superuser or hasattr(user, 'admin_profile')):
                fields.pop('admin_notes', None)
            
            # Hide vendor notes from customers
            if hasattr(user, 'customer_profile'):
                fields.pop('vendor_notes', None)
                
        return fields

    def validate(self, data):
        """Validate order item data"""
        if data['quantity'] <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")
        
        if data['price'] <= 0:
            raise serializers.ValidationError("Price must be greater than 0")
        
        # Check product belongs to the order's vendor
        order = self.context.get('order', None)
        if order and data['product'].vendor != order.vendor:
            raise serializers.ValidationError("Product does not belong to order vendor")
        
        return data


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    """Serializer for OrderStatusHistory model"""
    changed_by = UserSerializer(read_only=True)
    old_status_display = serializers.CharField(source='get_old_status_display', read_only=True)
    new_status_display = serializers.CharField(source='get_new_status_display', read_only=True)

    class Meta:
        model = OrderStatusHistory
        fields = [
            'id', 'order', 'old_status', 'old_status_display',
            'new_status', 'new_status_display', 'changed_by',
            'note', 'created_at'
        ]
        read_only_fields = fields


class OrderAssignmentHistorySerializer(serializers.ModelSerializer):
    """Serializer for OrderAssignmentHistory model"""
    assigned_to = UserSerializer(read_only=True)
    assigned_by = UserSerializer(read_only=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(vendor_employee__isnull=False),
        source='assigned_to',
        write_only=True
    )

    class Meta:
        model = OrderAssignmentHistory
        fields = [
            'id', 'order', 'assigned_to', 'assigned_to_id',
            'assigned_by', 'created_at', 'ended_at', 'active'
        ]
        read_only_fields = ['assigned_by', 'created_at', 'ended_at', 'active']


class OrderSerializer(serializers.ModelSerializer):
    """Main Order serializer with nested relationships"""
    customer = UserSerializer(read_only=True)
    vendor = VendorProfileSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    last_updated_by = UserSerializer(read_only=True)
    
    items = OrderItemSerializer(many=True, required=False)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    assignment_history = OrderAssignmentHistorySerializer(many=True, read_only=True)
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    
    available_status_actions = serializers.SerializerMethodField()
    
    customer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.Role.CUSTOMER),
        source='customer',
        write_only=True
    )
    vendor_id = serializers.PrimaryKeyRelatedField(
        queryset=Vendor.objects.all(),
        source='vendor',
        write_only=True
    )
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(vendor_employee__isnull=False),
        source='assigned_to',
        write_only=True,
        allow_null=True
    )

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer', 'customer_id', 'vendor', 'vendor_id',
            'status', 'status_display', 'payment_method', 'payment_method_display',
            'subtotal', 'tax_amount', 'shipping_cost', 'discount_amount', 'total',
            'assigned_to', 'assigned_to_id', 'last_updated_by',
            'created_at', 'updated_at', 'status_changed_at',
            'items', 'status_history', 'assignment_history',
            'available_status_actions'
        ]
        read_only_fields = [
            'order_number', 'subtotal', 'tax_amount', 'total',
            'last_updated_by', 'created_at', 'updated_at', 'status_changed_at'
        ]
        extra_kwargs = {
            'payment_method': {'required': False}
        }

    def get_available_status_actions(self, obj):
        """Get available status actions for the current user"""
        request = self.context.get('request', None)
        if request and hasattr(request, 'user'):
            return obj.get_status_actions(request.user)
        return []

    def validate(self, data):
        """Validate order data"""
        # Ensure customer can't be changed after creation
        if self.instance and 'customer' in data:
            raise serializers.ValidationError("Customer cannot be changed after order creation")
        
        # Validate vendor assignment
        if 'vendor' in data:
            vendor = data['vendor']
            if hasattr(self.context['request'].user, 'vendor') and self.context['request'].user.vendor != vendor:
                raise serializers.ValidationError("You can only create orders for your own vendor account")
        
        return data

    def create(self, validated_data):
        """Create order with items"""
        items_data = validated_data.pop('items', [])
        order = Order.objects.create(**validated_data)
        
        # Create order items
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        
        # Update totals
        order._calculate_totals()
        order.save()
        
        return order

    def update(self, instance, validated_data):
        """Update order with status change tracking"""
        request = self.context.get('request', None)
        new_status = validated_data.get('status', None)
        
        if new_status and new_status != instance.status:
            # Validate status transition
            if request and new_status not in instance.get_status_actions(request.user):
                raise serializers.ValidationError("Invalid status transition for your user role")
            
            # Track who made the change
            validated_data['last_updated_by'] = request.user if request else None
        
        return super().update(instance, validated_data)


class VendorOrderDashboardSerializer(serializers.ModelSerializer):
    """Serializer for VendorOrderDashboard model"""
    vendor = VendorProfileSerializer(read_only=True)

    class Meta:
        model = VendorOrderDashboard
        fields = [
            'id', 'vendor', 'default_status_filter',
            'show_unassigned_orders', 'show_assigned_to_others',
            'notify_new_orders', 'notify_assigned_orders',
            'notify_status_changes'
        ]
        read_only_fields = ['vendor']


class OrderPermissionSerializer(serializers.ModelSerializer):
    """Serializer for OrderPermission model"""
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = OrderPermission
        fields = [
            'id', 'role', 'role_display',
            'can_view_orders', 'can_edit_order_items', 'can_update_status',
            'can_assign_orders', 'can_view_customer_info', 'can_view_financials',
            'can_process_refunds', 'can_manage_returns'
        ]


class OrderStatusUpdateSerializer(serializers.Serializer):
    """Specialized serializer for updating order status"""
    new_status = serializers.ChoiceField(choices=Order.Status.choices)
    note = serializers.CharField(required=False, allow_blank=True)

    def validate_new_status(self, value):
        """Validate the new status is allowed"""
        order = self.context.get('order')
        request = self.context.get('request')
        
        if order and request and value not in order.get_status_actions(request.user):
            raise serializers.ValidationError("Invalid status transition for your user role")
        return value

    def update(self, instance, validated_data):
        """Update the order status"""
        request = self.context.get('request')
        instance.update_status(
            validated_data['new_status'],
            request.user,
            validated_data.get('note', '')
        )
        return instance


class OrderAssignmentSerializer(serializers.Serializer):
    """Specialized serializer for assigning orders"""
    employee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(vendor_employee__isnull=False)
    )

    def validate_employee_id(self, value):
        """Validate the employee can be assigned"""
        order = self.context.get('order')
        if order and value.vendor_employee.vendor != order.vendor:
            raise serializers.ValidationError("Cannot assign to employee from another vendor")
        return value

    def update(self, instance, validated_data):
        """Assign the order to an employee"""
        request = self.context.get('request')
        instance.assign_to_employee(
            validated_data['employee_id'],
            request.user
        )
        return instance


class OrderSummarySerializer(serializers.Serializer):
    """Serializer for order summary statistics"""
    status = serializers.CharField()
    count = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)


class OrderExportSerializer(serializers.ModelSerializer):
    """Serializer for order data export"""
    customer_email = serializers.EmailField(source='customer.email')
    vendor_name = serializers.CharField(source='vendor.user.company_name')
    assigned_to_email = serializers.EmailField(source='assigned_to.email', allow_null=True)
    status_display = serializers.CharField(source='get_status_display')

    class Meta:
        model = Order
        fields = [
            'order_number', 'customer_email', 'vendor_name',
            'status', 'status_display', 'total',
            'created_at', 'updated_at', 'assigned_to_email'
        ]
        read_only_fields = ['order_number', 'created_at', 'updated_at']

    def to_representation(self, instance):
        """Customize representation for export"""
        representation = super().to_representation(instance)
        representation['created_at'] = instance.created_at.strftime('%Y-%m-%d %H:%M:%S')
        representation['updated_at'] = instance.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        return representation