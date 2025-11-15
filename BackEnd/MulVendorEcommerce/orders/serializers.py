from rest_framework import serializers
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from django.core.validators import RegexValidator
from .models import (
    Order, 
    OrderItem, 
    OrderStatusHistory,
    OrderAssignmentHistory,
    VendorOrderDashboard,
    VendorOrderAnalytics,
    OrderPermission
)
from Users.models import User, Vendor, Address
from products.models import Product, ProductVariant
from Users.serializers import UserSerializer, VendorProfileSerializer
from products.serializers import ProductSerializer, ProductVariantSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for Order Items with detailed product/variant information"""
    product = serializers.SerializerMethodField()
    variant = serializers.SerializerMethodField()
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.only('id', 'name', 'price', 'vendor'),
        source='product',
        write_only=True
    )
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.only('id', 'name', 'price'),
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
        read_only_fields = ['total', 'order']
        extra_kwargs = {
            'price': {'min_value': Decimal('0.01')},
            'vendor_notes': {'required': False, 'allow_blank': True},
            'admin_notes': {'required': False, 'allow_blank': True}
        }

    def get_product(self, obj):
        """Get simplified product representation"""
        return {
            'id': obj.product.id,
            'name': obj.product.name,
            'price': str(obj.product.price),
            'vendor_id': obj.product.vendor.id
        }

    def get_variant(self, obj):
        """Get simplified variant representation if exists"""
        if obj.variant:
            return {
                'id': obj.variant.id,
                'name': obj.variant.name,
                'price': str(obj.variant.price)
            }
        return None

    def validate(self, data):
        """Validate order item data"""
        request = self.context.get('request')
        order = self.instance.order if self.instance else self.context.get('order')
        
        if data['quantity'] <= 0:
            raise serializers.ValidationError({
                'quantity': "Quantity must be greater than 0"
            })
        
        if order and data['product'].vendor != order.vendor:
            raise serializers.ValidationError({
                'product': "Product must belong to order's vendor"
            })
        
        if request and request.user.is_authenticated:
            if hasattr(request.user, 'customer_profile') and 'vendor_notes' in data:
                raise serializers.ValidationError({
                    'vendor_notes': "Customers cannot set vendor notes"
                })
            
            if hasattr(request.user, 'vendor_employee') and not request.user.vendor_employee.can_edit_order_items:
                raise serializers.ValidationError({
                    'admin_notes': "Vendor employees cannot set admin notes"
                })
        
        return data


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    """Serializer for tracking order status changes"""
    changed_by = serializers.SerializerMethodField()
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

    def get_changed_by(self, obj):
        """Get simplified user information for who changed the status"""
        if obj.changed_by:
            return {
                'id': obj.changed_by.id,
                'email': obj.changed_by.email,
                'name': obj.changed_by.get_full_name()
            }
        return None


class OrderAssignmentHistorySerializer(serializers.ModelSerializer):
    """Serializer for tracking order assignment history"""
    assigned_to = serializers.SerializerMethodField()
    assigned_by = serializers.SerializerMethodField()
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(vendor_employee__isnull=False).only('id'),
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

    def get_assigned_to(self, obj):
        """Get simplified assigned user information"""
        if obj.assigned_to:
            return {
                'id': obj.assigned_to.id,
                'email': obj.assigned_to.email,
                'name': obj.assigned_to.get_full_name()
            }
        return None

    def get_assigned_by(self, obj):
        """Get simplified assigner user information"""
        if obj.assigned_by:
            return {
                'id': obj.assigned_by.id,
                'email': obj.assigned_by.email,
                'name': obj.assigned_by.get_full_name()
            }
        return None


class VendorOrderDashboardSerializer(serializers.ModelSerializer):
    """Serializer for vendor dashboard configuration"""
    vendor = serializers.SerializerMethodField()
    
    class Meta:
        model = VendorOrderDashboard
        fields = [
            'id', 'vendor', 'default_status_filter',
            'show_unassigned_orders', 'show_assigned_to_others',
            'notify_new_orders', 'notify_assigned_orders',
            'notify_status_changes'
        ]
        read_only_fields = ['vendor']

    def get_vendor(self, obj):
        """Get simplified vendor information"""
        return {
            'id': obj.vendor.id,
            'business_name': obj.vendor.company_name
        }


class VendorOrderAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for vendor order analytics"""
    vendor = serializers.SerializerMethodField()
    
    class Meta:
        model = VendorOrderAnalytics
        fields = [
            'id', 'vendor', 'total_orders', 'total_revenue',
            'average_order_value', 'total_items_sold', 'last_updated'
        ]
        read_only_fields = fields

    def get_vendor(self, obj):
        """Get simplified vendor information"""
        return {
            'id': obj.vendor.id,
            'business_name': obj.vendor.company_name
        }


class OrderPermissionSerializer(serializers.ModelSerializer):
    """Serializer for order permissions configuration"""
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = OrderPermission
        fields = [
            'id', 'role', 'role_display',
            'can_view_orders', 'can_edit_order_items', 'can_update_status',
            'can_assign_orders', 'can_view_customer_info', 'can_view_financials',
            'can_process_refunds', 'can_manage_returns'
        ]


class OrderAddressSerializer(serializers.ModelSerializer):
    """Serializer for order-related addresses with validation"""
    class Meta:
        model = Address
        fields = [
            'id', 'recipient_name', 'company_name',
            'street_address', 'apartment_address', 
            'city', 'state', 'postal_code', 'country',
            'is_default', 'phone'
        ]
        read_only_fields = ['id']
        extra_kwargs = {
            'street_address': {'required': True},
            'city': {'required': True},
            'postal_code': {'required': True},
            'country': {'required': True},
            'phone': {
                'validators': [
                    RegexValidator(
                        regex=r'^\+?1?\d{9,15}$',
                        message="Phone number must be in format: '+999999999'. Up to 15 digits."
                    )
                ]
            }
        }
        ref_name = 'OrderAddress'

    def validate(self, data):
        """Validate address data"""
        if not data.get('street_address') and not data.get('apartment_address'):
            raise serializers.ValidationError(
                "Either street address or apartment address must be provided"
            )
        return data


class OrderSerializer(serializers.ModelSerializer):
    """Comprehensive order serializer with nested relationships"""
    customer = serializers.SerializerMethodField()
    vendor = serializers.SerializerMethodField()
    assigned_to = serializers.SerializerMethodField()
    last_updated_by = serializers.SerializerMethodField()
    shipping_address = OrderAddressSerializer(read_only=True)
    billing_address = OrderAddressSerializer(read_only=True)
    
    items = OrderItemSerializer(many=True, required=False)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    assignment_history = OrderAssignmentHistorySerializer(many=True, read_only=True)
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(
        source='get_payment_method_display', 
        read_only=True
    )
    available_status_actions = serializers.SerializerMethodField()
    
    # Write-only fields for ID-based relationships
    shipping_address_id = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.all(),
        source='shipping_address',
        write_only=True,
        required=False,
        allow_null=True
    )
    billing_address_id = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.all(),
        source='billing_address',
        write_only=True,
        required=False,
        allow_null=True
    )
    customer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.Role.CUSTOMER).only('id'),
        source='customer',
        write_only=True
    )
    vendor_id = serializers.PrimaryKeyRelatedField(
        queryset=Vendor.objects.only('id'),
        source='vendor',
        write_only=True
    )
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(vendor_employee__isnull=False).only('id'),
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
            'customer_notes', 'vendor_notes', 'admin_notes',
            'assigned_to', 'assigned_to_id', 'last_updated_by',
            'shipping_address', 'shipping_address_id',
            'billing_address', 'billing_address_id',
            'created_at', 'updated_at', 'status_changed_at',
            'items', 'status_history', 'assignment_history',
            'available_status_actions'
        ]
        read_only_fields = [
            'order_number', 'subtotal', 'tax_amount', 'total',
            'last_updated_by', 'created_at', 'updated_at', 'status_changed_at'
        ]
        extra_kwargs = {
            'customer_notes': {'required': False, 'allow_blank': True},
            'vendor_notes': {'required': False, 'allow_blank': True},
            'admin_notes': {'required': False, 'allow_blank': True}
        }

    def get_customer(self, obj):
        """Get simplified customer information"""
        if obj.customer:
            return {
                'id': obj.customer.id,
                'email': obj.customer.email,
                'name': obj.customer.get_full_name(),
                'phone': obj.customer.phone_number
            }
        return None

    def get_vendor(self, obj):
        """Get simplified vendor information"""
        if obj.vendor:
            return {
                'id': obj.vendor.id,
                'business_name': obj.vendor.company_name,
                'contact_email': obj.vendor.business_email,
                'contact_phone': obj.vendor.business_phone
            }
        return None

    def get_assigned_to(self, obj):
        """Get simplified assigned employee information"""
        if obj.assigned_to:
            return {
                'id': obj.assigned_to.id,
                'email': obj.assigned_to.email,
                'name': obj.assigned_to.get_full_name(),
                'role': obj.assigned_to.vendor_employee.get_role_display()
            }
        return None

    def get_last_updated_by(self, obj):
        """Get simplified user information for who last updated the order"""
        if obj.last_updated_by:
            return {
                'id': obj.last_updated_by.id,
                'email': obj.last_updated_by.email,
                'name': obj.last_updated_by.get_full_name(),
                'role': obj.last_updated_by.role
            }
        return None

    def get_available_status_actions(self, obj):
        """Get available status transitions based on user permissions"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_status_actions(request.user)
        return []

    def validate(self, data):
        """Validate order data including address ownership"""
        customer = data.get('customer', getattr(self.instance, 'customer', None))
        
        if customer:
            # Validate shipping address belongs to customer
            if 'shipping_address' in data and data['shipping_address']:
                if data['shipping_address'].user != customer:
                    raise serializers.ValidationError({
                        'shipping_address_id': "Shipping address must belong to the customer"
                    })
            
            # Validate billing address belongs to customer
            if 'billing_address' in data and data['billing_address']:
                if data['billing_address'].user != customer:
                    raise serializers.ValidationError({
                        'billing_address_id': "Billing address must belong to the customer"
                    })
        
        # Validate notes permissions based on user role
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if hasattr(request.user, 'customer_profile'):
                if 'vendor_notes' in data or 'admin_notes' in data:
                    raise serializers.ValidationError({
                        'detail': "Customers can only add customer notes"
                    })
            
            if hasattr(request.user, 'vendor_employee'):
                if 'admin_notes' in data and not request.user.vendor_employee.can_edit_order_items:
                    raise serializers.ValidationError({
                        'admin_notes': "You don't have permission to add admin notes"
                    })
        
        return data

    @transaction.atomic
    def create(self, validated_data):
        """Create order with transaction safety"""
        items_data = validated_data.pop('items', [])
        order = Order.objects.create(**validated_data)
        
        # Bulk create order items for performance
        OrderItem.objects.bulk_create([
            OrderItem(order=order, **item_data)
            for item_data in items_data
        ])
        
        # Calculate and save totals
        order._calculate_totals()
        order.save()
        return order

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update order with status transition validation"""
        request = self.context.get('request')
        new_status = validated_data.get('status')
        
        # Handle status transitions
        if new_status and new_status != instance.status:
            if request and new_status not in instance.get_status_actions(request.user):
                raise serializers.ValidationError({
                    'status': "Invalid status transition for your role"
                })
            
            validated_data['last_updated_by'] = request.user
            validated_data['status_changed_at'] = timezone.now()
        
        return super().update(instance, validated_data)