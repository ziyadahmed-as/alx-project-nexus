import uuid
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.db.models import Sum, F, Q
from django.core.cache import cache
from django.utils import timezone
from decimal import Decimal
# In orders/models.py
from Users.models import User, Vendor
from django.core.exceptions import ValidationError

class Order(models.Model):
    """Enhanced Order model with multi-role tracking and management"""
    
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', _('Draft')
        PENDING_PAYMENT = 'PENDING_PAYMENT', _('Pending Payment')
        PAYMENT_RECEIVED = 'PAYMENT_RECEIVED', _('Payment Received')
        PROCESSING = 'PROCESSING', _('Processing')
        READY_FOR_SHIPMENT = 'READY_FOR_SHIPMENT', _('Ready for Shipment')
        SHIPPED = 'SHIPPED', _('Shipped')
        OUT_FOR_DELIVERY = 'OUT_FOR_DELIVERY', _('Out for Delivery')
        DELIVERED = 'DELIVERED', _('Delivered')
        CANCELLED = 'CANCELLED', _('Cancelled')
        RETURN_REQUESTED = 'RETURN_REQUESTED', _('Return Requested')
        RETURN_APPROVED = 'RETURN_APPROVED', _('Return Approved')
        RETURN_RECEIVED = 'RETURN_RECEIVED', _('Return Received')
        REFUNDED = 'REFUNDED', _('Refunded')
        ON_HOLD = 'ON_HOLD', _('On Hold')
        FAILED = 'FAILED', _('Failed')

    class PaymentMethod(models.TextChoices):
        CHAPA = 'CHAPA', _('Chapa')
        CASH_ON_DELIVERY = 'CASH_ON_DELIVERY', _('Cash on Delivery')
        BANK_TRANSFER = 'BANK_TRANSFER', _('Bank Transfer')
        WALLET = 'WALLET', _('Wallet')

    # Core Order Fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey('Users.User', on_delete=models.PROTECT, related_name='customer_orders')
    vendor = models.ForeignKey('Users.Vendor', on_delete=models.PROTECT, related_name='vendor_orders')
    
    # Status Tracking
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, null=True, blank=True)
    
    # Financial Fields
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Notes Fields (Added to fix the serializer error)
    customer_notes = models.TextField(blank=True, help_text=_("Notes from the customer"))
    vendor_notes = models.TextField(blank=True, help_text=_("Internal notes for vendor"))
    admin_notes = models.TextField(blank=True, help_text=_("Notes for administrators"))
    
    # Address Fields
    shipping_address = models.ForeignKey(
        'Users.Address', 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shipping_orders'
    )
    billing_address = models.ForeignKey(
        'Users.Address',  
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='billing_orders'
    )
    
    # Tracking Fields
    assigned_to = models.ForeignKey(
        'Users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_orders',
        help_text=_("Vendor employee currently handling this order")
    )
    last_updated_by = models.ForeignKey(
        'Users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_orders'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status_changed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['vendor', 'status']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['status', 'status_changed_at']),
        ]
        permissions = [
            ('view_all_orders', 'Can view all orders (Admin)'),
            ('view_vendor_orders', 'Can view vendor orders'),
            ('change_order_status', 'Can change order status'),
            ('assign_order', 'Can assign orders to employees'),
        ]

    def __str__(self):
        return f"Order #{self.order_number} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self._generate_order_number()
        
        if 'status' in self.get_dirty_fields():
            self.status_changed_at = timezone.now()
        
        self._calculate_totals()
        super().save(*args, **kwargs)
        self._update_caches()

    def _generate_order_number(self):
        """Generate unique order number with vendor prefix"""
        vendor_prefix = self.vendor.user.username[:3].upper()
        timestamp = timezone.now().strftime('%y%m%d')
        random_part = str(uuid.uuid4().int)[:6]
        return f"{vendor_prefix}-{timestamp}-{random_part}"

    def _calculate_totals(self):
        """Calculate order totals based on items"""
        if self.status == self.Status.DRAFT:
            items = self.items.all()
            self.subtotal = items.aggregate(total=Sum(F('price') * F('quantity')))['total'] or Decimal('0.00')
            self.total = self.subtotal + self.tax_amount + self.shipping_cost - self.discount_amount

    def _update_caches(self):
        """Update all related caches for this order"""
        cache_keys = [
            f'order_{self.id}',
            f'vendor_{self.vendor_id}_orders',
            f'customer_{self.customer_id}_orders',
        ]
        if self.assigned_to:
            cache_keys.append(f'employee_{self.assigned_to_id}_orders')
        
        for key in cache_keys:
            cache.set(key, self, 3600)

    def clean(self):
        """Validate model before saving"""
        if self.billing_address and self.shipping_address:
            if self.billing_address.user != self.customer or self.shipping_address.user != self.customer:
                raise ValidationError(_("Addresses must belong to the customer"))

class OrderItem(models.Model):
    """Order line items with role-based visibility"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT)
    variant = models.ForeignKey('products.ProductVariant', on_delete=models.PROTECT, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Vendor-specific fields
    vendor_notes = models.TextField(blank=True, help_text=_("Internal notes for vendor"))
    admin_notes = models.TextField(blank=True, help_text=_("Notes for administrators"))
    
    class Meta:
        verbose_name = _('Order Item')
        verbose_name_plural = _('Order Items')
        indexes = [
            models.Index(fields=['order', 'product']),
        ]

    def save(self, *args, **kwargs):
        self.total = (self.price * self.quantity) + self.tax_amount - self.discount_amount
        super().save(*args, **kwargs)

    def clean(self):
        """Validate product belongs to order vendor"""
        if self.product.vendor != self.order.vendor:
            raise ValidationError(_("Product must belong to the order's vendor"))


class OrderStatusHistory(models.Model):
    """Track all status changes with role information"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=20, choices=Order.Status.choices)
    new_status = models.CharField(max_length=20, choices=Order.Status.choices)
    changed_by = models.ForeignKey('Users.User', on_delete=models.SET_NULL, null=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Order Status History')
        verbose_name_plural = _('Order Status Histories')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.order} status changed from {self.old_status} to {self.new_status}"


class OrderAssignmentHistory(models.Model):
    """Track order assignments to vendor employees"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='assignment_history')
    assigned_to = models.ForeignKey('Users.User', on_delete=models.SET_NULL, null=True, related_name='assigned_order_history')
    assigned_by = models.ForeignKey('Users.User', on_delete=models.SET_NULL, null=True, related_name='order_assignments_made')
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _('Order Assignment')
        verbose_name_plural = _('Order Assignments')
        ordering = ['-created_at']
    
    def end_assignment(self, ended_by):
        """Mark assignment as ended"""
        self.ended_at = timezone.now()
        self.active = False
        self.assigned_by = ended_by
        self.save()


class VendorOrderDashboard(models.Model):
    """Vendor-specific order dashboard configuration"""
    vendor = models.OneToOneField('Users.Vendor', on_delete=models.CASCADE)
    
    # Display preferences
    default_status_filter = models.CharField(
        max_length=20,
        choices=Order.Status.choices,
        default=Order.Status.PROCESSING
    )
    show_unassigned_orders = models.BooleanField(default=True)
    show_assigned_to_others = models.BooleanField(default=False)
    
    # Notification preferences
    notify_new_orders = models.BooleanField(default=True)
    notify_assigned_orders = models.BooleanField(default=True)
    notify_status_changes = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _('Vendor Order Dashboard')
        verbose_name_plural = _('Vendor Order Dashboards')
    
    def __str__(self):
        return f"Order Dashboard for {self.vendor}"


class OrderPermission(models.Model):
    """Granular permissions for vendor employees"""
    ROLE_CHOICES = [
        ('MANAGER', 'Manager'),
        ('STAFF', 'Staff'),
        ('CUSTOMER_SERVICE', 'Customer Service'),
        ('DELIVERY', 'Delivery'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True)
    
    # Permissions
    can_view_orders = models.BooleanField(default=True)
    can_edit_order_items = models.BooleanField(default=False)
    can_update_status = models.BooleanField(default=False)
    can_assign_orders = models.BooleanField(default=False)
    can_view_customer_info = models.BooleanField(default=True)
    can_view_financials = models.BooleanField(default=False)
    can_process_refunds = models.BooleanField(default=False)
    can_manage_returns = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = _('Order Permission')
        verbose_name_plural = _('Order Permissions')
    
    def __str__(self):
        return f"Permissions for {self.get_role_display()}"

class VendorOrderAnalytics(models.Model):
    vendor = models.OneToOneField(Vendor, on_delete=models.CASCADE, related_name='order_analytics')
    total_orders = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_items_sold = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Vendor Order Analytics"
    def update_analytics(self):
        """Update analytics based on current orders"""
        orders = self.vendor.vendor_orders.filter(status__in=[
            Order.Status.DELIVERED, Order.Status.REFUNDED, Order.Status.CANCELLED
        ])

    def __str__(self):
        return f"Analytics for {self.vendor.user.business_name}"
        self.total_orders = orders.count()
        self.total_revenue = orders.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
        self.average_order_value = (self.total_revenue / self.total_orders) if self.total_orders else Decimal('0.00')
        self.total_items_sold = orders.aggregate(total=Sum('items__quantity'))['total'] or 0
        self.save() 
        return f"Analytics for {self.vendor.user.business_name}"
    
    def clean(self):
        """Validate that vendor exists and has orders"""
        if not self.vendor or not self.vendor.vendor_orders.exists():
            raise ValidationError(_("Vendor must have at least one order to create analytics"))
        return bool(
            self.vendor and self.vendor.vendor_orders.exists()
        )
    def has_permission(self, request, view):
        """Check if user has permission to view vendor orders"""    
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'vendor_employee'):
            return request.user.vendor_employee.vendor == self.vendor   
        return False
        return bool(
            request.user.is_authenticated and
            hasattr(request.user, 'vendor') and
            request.user.vendor == self.vendor
        )   
        
             
# Signal handlers
@receiver(post_save, sender=Order)
def handle_order_status_change(sender, instance, **kwargs):
    """Handle notifications and workflows when order status changes"""
    if 'status' in instance.get_dirty_fields():
        # Notify relevant parties based on status change
        pass


@receiver(post_save, sender='Users.VendorEmployee')
def setup_employee_permissions(sender, instance, created, **kwargs):
    """Set up default permissions for new vendor employees"""
    if created:
        try:
            permission = OrderPermission.objects.get(role=instance.role)
            # Apply permissions to employee
        except OrderPermission.DoesNotExist:
            pass


@receiver(post_save, sender='Users.Vendor')
def setup_vendor_order_dashboard(sender, instance, created, **kwargs):
    """Set up default order dashboard for new vendors"""
    if created:
        VendorOrderDashboard.objects.create(
            vendor=instance,
            default_status_filter=Order.Status.PROCESSING,
            show_unassigned_orders=True,
            show_assigned_to_others=False,
            notify_new_orders=True,
            notify_assigned_orders=True,
            notify_status_changes=True
        )