from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.utils.text import slugify
import uuid
from django.core.cache import cache
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

class Category(models.Model):
    """Hierarchical product category system with caching support"""
    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['slug']),
        ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    description = models.TextField(blank=True)
    parent_category = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='subcategories',
        on_delete=models.SET_NULL
    )
    image = models.ImageField(upload_to='category_images/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        self._update_caches()

    def delete(self, *args, **kwargs):
        self._clear_caches()
        super().delete(*args, **kwargs)

    def _update_caches(self):
        """Update all related caches for this category"""
        cache.set(f'category_{self.id}', self, 3600)
        cache.delete('all_categories')

    def _clear_caches(self):
        """Clear all cached data for this category"""
        cache.delete(f'category_{self.id}')
        cache.delete('all_categories')

    @classmethod
    def get_cached(cls, category_id):
        """Retrieve category with cache support"""
        cache_key = f'category_{category_id}'
        category = cache.get(cache_key)
        if not category:
            category = cls.objects.get(id=category_id)
            cache.set(cache_key, category, 3600)
        return category


class Product(models.Model):
    """Core product model with comprehensive caching and vendor integration"""
    class Condition(models.TextChoices):
        NEW = 'NEW', _('New')
        USED = 'USED', _('Used')
        REFURBISHED = 'REFURBISHED', _('Refurbished')

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', _('Draft')
        PENDING = 'PENDING', _('Pending Approval')
        APPROVED = 'APPROVED', _('Approved')
        REJECTED = 'REJECTED', _('Rejected')
        ARCHIVED = 'ARCHIVED', _('Archived')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(
        'Users.Vendor',
        on_delete=models.CASCADE,
        related_name='products',
        db_index=True
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products',
        db_index=True
    )
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=300, unique=True, blank=True, db_index=True)
    description = models.TextField()
    short_description = models.CharField(max_length=200, blank=True)
    sku = models.CharField(max_length=100, unique=True, db_index=True)
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        db_index=True
    )
    compare_at_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    cost_per_item = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    condition = models.CharField(
        max_length=20,
        choices=Condition.choices,
        default=Condition.NEW,
        db_index=True
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True
    )
    quantity = models.PositiveIntegerField(default=0, db_index=True)
    weight = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Weight in kilograms')
    )
    is_active = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    is_digital = models.BooleanField(default=False)
    rating = models.FloatField(default=0.0, db_index=True)
    view_count = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(
        'Users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_products',
        db_index=True
    )
    updated_by = models.ForeignKey(
        'Users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_products',
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Product')
        verbose_name_plural = _('Products')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['price', 'is_active']),
            models.Index(fields=['rating', 'is_active']),
            models.Index(fields=['vendor', 'status']),
            models.Index(fields=['created_by', 'status']),
        ]

    def __str__(self):
        return f"{self.name} - {self.vendor.user.email}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.name}-{str(self.id)[:8]}")
            self.slug = base_slug
        
        # Track who is modifying the product
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
            
        super().save(*args, **kwargs)
        self._update_caches()

    def delete(self, *args, **kwargs):
        self._clear_caches()
        super().delete(*args, **kwargs)

    def _update_caches(self):
        """Update all related caches for this product"""
        cache.set(f'product_{self.id}', self, 3600)
        cache.delete(f'vendor_{self.vendor_id}_products')
        cache.delete(f'category_{self.category_id}_products')

    def _clear_caches(self):
        """Clear all cached data for this product"""
        cache.delete_pattern(f'product_{self.id}*')
        cache.delete(f'vendor_{self.vendor_id}_products')
        cache.delete(f'category_{self.category_id}_products')

    @property
    def is_available(self):
        """Check if product is available for purchase"""
        return (self.is_active and 
                self.status == self.Status.APPROVED and 
                self.quantity > 0)

    @property
    def discount_percentage(self):
        """Calculate discount percentage if compare price exists"""
        if self.compare_at_price and self.compare_at_price > self.price:
            return round(((self.compare_at_price - self.price) / self.compare_at_price) * 100)
        return 0

    @classmethod
    def get_cached(cls, product_id):
        """Retrieve product with cache support"""
        cache_key = f'product_{product_id}'
        product = cache.get(cache_key)
        if not product:
            product = cls.objects.select_related('vendor', 'category').get(id=product_id)
            cache.set(cache_key, product, 3600)
        return product

    # Product management permissions
    @staticmethod
    def can_create_product(user):
        """Check if user can create a product"""
        return (hasattr(user, 'vendor') or 
               (hasattr(user, 'vendor_employee') and 
                user.vendor_employee.role) in ['MANAGER', 'STAFF'])

    @staticmethod
    def can_edit_product(user, product):
        """Check if user can edit a product"""
        if user.is_superuser:
            return True
        if hasattr(user, 'admin_profile'):
            return True
        if hasattr(user, 'vendor') and product.vendor == user.vendor:
            return True
        if (hasattr(user, 'vendor_employee') and 
            product.vendor == user.vendor_employee.vendor and
            user.vendor_employee.role in ['MANAGER', 'STAFF']):
            return True
        return False

    @staticmethod
    def can_change_status(user, product):
        """Check if user can change product status"""
        if user.is_superuser:
            return True
        if hasattr(user, 'admin_profile'):
            return True
        if hasattr(user, 'vendor') and product.vendor == user.vendor:
            return user.vendor.verification_status == 'VERIFIED'
        return False

    @staticmethod
    def can_delete_product(user, product):
        """Check if user can delete a product"""
        if user.is_superuser:
            return True
        if hasattr(user, 'admin_profile'):
            return True
        if hasattr(user, 'vendor') and product.vendor == user.vendor:
            return True
        if (hasattr(user, 'vendor_employee') and 
            product.vendor == user.vendor_employee.vendor and
            user.vendor_employee.role == 'MANAGER'):
            return True
        return False


class ProductImage(models.Model):
    """Product image gallery with caching and permission control"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        db_index=True
    )
    image = models.ImageField(upload_to='product_images/')
    alt_text = models.CharField(max_length=125, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    uploaded_by = models.ForeignKey(
        'Users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_product_images',
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = _('Product Image')
        verbose_name_plural = _('Product Images')
        ordering = ['order']
        unique_together = ('product', 'order')

    def __str__(self):
        return f"Image for {self.product.name}"

    def save(self, *args, **kwargs):
        if not self.pk:  # Only on creation
            user = kwargs.pop('user', None)
            if user:
                self.uploaded_by = user
        
        if self.is_primary:
            self.__class__.objects.filter(
                product=self.product,
                is_primary=True
            ).update(is_primary=False)
            
        super().save(*args, **kwargs)
        cache.delete(f'product_{self.product_id}_images')

    def delete(self, *args, **kwargs):
        cache.delete(f'product_{self.product_id}_images')
        super().delete(*args, **kwargs)

    @staticmethod
    def can_add_image(user, product):
        """Check if user can add image to product"""
        if user.is_superuser:
            return True
        if hasattr(user, 'admin_profile'):
            return True
        if hasattr(user, 'vendor') and product.vendor == user.vendor:
            return True
        if (hasattr(user, 'vendor_employee') and 
            product.vendor == user.vendor_employee.vendor and
            user.vendor_employee.role in ['MANAGER', 'STAFF']):
            return True
        return False


class ProductVariant(models.Model):
    """Product variants with caching support"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants',
        db_index=True
    )
    name = models.CharField(max_length=100)
    sku = models.CharField(max_length=100, unique=True, db_index=True)
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        db_index=True
    )
    quantity = models.PositiveIntegerField(default=0, db_index=True)
    created_by = models.ForeignKey(
        'Users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_variants',
        db_index=True
    )
    updated_by = models.ForeignKey(
        'Users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_variants',
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Product Variant')
        verbose_name_plural = _('Product Variants')
        unique_together = ('product', 'name')

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
            
        super().save(*args, **kwargs)
        self._update_caches()

    def delete(self, *args, **kwargs):
        self._clear_caches()
        super().delete(*args, **kwargs)

    def _update_caches(self):
        """Update all related caches for this variant"""
        cache.set(f'variant_{self.id}', self, 3600)
        cache.delete(f'product_{self.product_id}_variants')

    def _clear_caches(self):
        """Clear all cached data for this variant"""
        cache.delete(f'variant_{self.id}')
        cache.delete(f'product_{self.product_id}_variants')

    @staticmethod
    def can_manage_variant(user, product):
        """Check if user can manage variants for a product"""
        return Product.can_edit_product(user, product)


class ProductReview(models.Model):
    """Product reviews with caching and user integration"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews',
        db_index=True
    )
    user = models.ForeignKey(
        'Users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='reviews',
        db_index=True
    )
    rating = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 6)],
        default=5,
        db_index=True
    )
    title = models.CharField(max_length=120)
    comment = models.TextField()
    vendor_response = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Product Review')
        verbose_name_plural = _('Product Reviews')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'is_approved']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"Review for {self.product.name} by {self.user.email if self.user else 'Anonymous'}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._update_caches()

    def delete(self, *args, **kwargs):
        self._clear_caches()
        super().delete(*args, **kwargs)

    def _update_caches(self):
        """Update all related caches for this review"""
        cache.set(f'review_{self.id}', self, 3600)
        cache.delete(f'product_{self.product_id}_reviews')
        cache.delete(f'user_{self.user_id}_reviews')

    def _clear_caches(self):
        """Clear all cached data for this review"""
        cache.delete(f'review_{self.id}')
        cache.delete(f'product_{self.product_id}_reviews')
        cache.delete(f'user_{self.user_id}_reviews')

    @staticmethod
    def can_approve_review(user, product):
        """Check if user can approve reviews for a product"""
        if user.is_superuser:
            return True
        if hasattr(user, 'admin_profile'):
            return True
        if hasattr(user, 'vendor') and product.vendor == user.vendor:
            return True
        if (hasattr(user, 'vendor_employee') and 
            product.vendor == user.vendor_employee.vendor and
            user.vendor_employee.role in ['MANAGER', 'CUSTOMER_SERVICE']):
            return True
        return False


class ProductQuestion(models.Model):
    """Product questions with caching and user integration"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='questions',
        db_index=True
    )
    user = models.ForeignKey(
        'Users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='questions',
        db_index=True
    )
    question = models.TextField()
    answer = models.TextField(blank=True)
    answered_by = models.ForeignKey(
        'Users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='answered_questions',
        db_index=True
    )
    is_approved = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Product Question')
        verbose_name_plural = _('Product Questions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'is_approved']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"Question about {self.product.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._update_caches()

    def delete(self, *args, **kwargs):
        self._clear_caches()
        super().delete(*args, **kwargs)

    def _update_caches(self):
        """Update all related caches for this question"""
        cache.set(f'question_{self.id}', self, 3600)
        cache.delete(f'product_{self.product_id}_questions')

    def _clear_caches(self):
        """Clear all cached data for this question"""
        cache.delete(f'question_{self.id}')
        cache.delete(f'product_{self.product_id}_questions')

    @staticmethod
    def can_answer_question(user, product):
        """Check if user can answer questions for a product"""
        if user.is_superuser:
            return True
        if hasattr(user, 'admin_profile'):
            return True
        if hasattr(user, 'vendor') and product.vendor == user.vendor:
            return True
        if (hasattr(user, 'vendor_employee') and 
            product.vendor == user.vendor_employee.vendor and
            user.vendor_employee.role in ['MANAGER', 'CUSTOMER_SERVICE']):
            return True
        return False


# Signal handlers for cache management
@receiver(post_save, sender=Product)
def product_post_save(sender, instance, **kwargs):
    """Update caches after product save"""
    instance._update_caches()

@receiver(post_delete, sender=Product)
def product_post_delete(sender, instance, **kwargs):
    """Clear cache when product is deleted"""
    instance._clear_caches()

@receiver(post_save, sender=ProductVariant)
def variant_post_save(sender, instance, **kwargs):
    """Update caches after variant save"""
    instance._update_caches()

@receiver(post_delete, sender=ProductVariant)
def variant_post_delete(sender, instance, **kwargs):
    """Clear cache when variant is deleted"""
    instance._clear_caches()