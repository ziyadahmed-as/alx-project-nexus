from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.utils.text import slugify
from Users.models import VendorProfile, User
import uuid
from django.core.cache import cache
from django.conf import settings

# Cache constants
CACHE_TTL = getattr(settings, 'CACHE_TTL', 60 * 15)  # 15 minutes default
CATEGORY_CACHE_KEY = "category_{id}"
PRODUCT_CACHE_KEY = "product_{id}"
PRODUCT_LIST_CACHE_KEY = "products_{vendor}_{status}_{page}"
PRODUCT_VARIANT_CACHE_KEY = "variant_{id}"
PRODUCT_REVIEW_CACHE_KEY = "review_{id}"
PRODUCT_QUESTION_CACHE_KEY = "question_{id}"

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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        # Update cache
        cache_key = CATEGORY_CACHE_KEY.format(id=self.id)
        cache.set(cache_key, self, CACHE_TTL)

    def delete(self, *args, **kwargs):
        # Clear cache
        cache_key = CATEGORY_CACHE_KEY.format(id=self.id)
        cache.delete(cache_key)
        super().delete(*args, **kwargs)

    @classmethod
    def get_cached(cls, category_id):
        cache_key = CATEGORY_CACHE_KEY.format(id=category_id)
        category = cache.get(cache_key)
        if not category:
            category = cls.objects.get(id=category_id)
            cache.set(cache_key, category, CACHE_TTL)
        return category

class Product(models.Model):
    """Core product model with Redis caching support"""
    class Condition(models.TextChoices):
        NEW = 'NEW', _('New')
        USED = 'USED', _('Used')
        REFURBISHED = 'REFURBISHED', _('Refurbished')

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', _('Draft')
        PENDING = 'PENDING', _('Pending Approval')
        APPROVED = 'APPROVED', _('Approved')
        REJECTED = 'REJECTED', _('Rejected')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(
        VendorProfile,
        on_delete=models.CASCADE,
        related_name='products'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products'
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    description = models.TextField()
    short_description = models.CharField(max_length=200, blank=True)
    sku = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
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
        default=Condition.NEW
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    quantity = models.PositiveIntegerField(default=0)
    weight = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Weight in kilograms')
    )
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_digital = models.BooleanField(default=False)
    rating = models.FloatField(default=0.0)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Product')
        verbose_name_plural = _('Products')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['slug']),
            models.Index(fields=['sku']),
            models.Index(fields=['price']),
            models.Index(fields=['is_active']),
            models.Index(fields=['rating']),
            models.Index(fields=['vendor']),
        ]

    def __str__(self):
        return f"{self.name} - {self.vendor.business_name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.name}-{self.vendor.business_name}")
            self.slug = base_slug
            counter = 1
            while Product.objects.filter(slug=self.slug).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)
        # Update cache
        cache_key = PRODUCT_CACHE_KEY.format(id=self.id)
        cache.set(cache_key, self, CACHE_TTL)
        # Clear product list cache for this vendor
        self.clear_vendor_product_cache()

    def delete(self, *args, **kwargs):
        # Clear caches
        cache_key = PRODUCT_CACHE_KEY.format(id=self.id)
        cache.delete(cache_key)
        self.clear_vendor_product_cache()
        super().delete(*args, **kwargs)

    def clear_vendor_product_cache(self):
        """Clear all cached product lists for this vendor"""
        cache.delete_pattern(PRODUCT_LIST_CACHE_KEY.format(
            vendor=self.vendor_id,
            status='*',
            page='*'
        ))

    @classmethod
    def get_cached(cls, product_id):
        cache_key = PRODUCT_CACHE_KEY.format(id=product_id)
        product = cache.get(cache_key)
        if not product:
            product = cls.objects.select_related('vendor', 'category').get(id=product_id)
            cache.set(cache_key, product, CACHE_TTL)
        return product

    @classmethod
    def get_vendor_products_cached(cls, vendor_id, status=None, page=1):
        cache_key = PRODUCT_LIST_CACHE_KEY.format(
            vendor=vendor_id,
            status=status or 'all',
            page=page
        )
        products = cache.get(cache_key)
        if not products:
            queryset = cls.objects.filter(vendor_id=vendor_id)
            if status:
                queryset = queryset.filter(status=status)
            products = list(queryset.order_by('-created_at'))
            cache.set(cache_key, products, CACHE_TTL)
        return products

    @property
    def is_available(self):
        return self.is_active and self.status == self.Status.APPROVED and self.quantity > 0

    @property
    def discount_percentage(self):
        if self.compare_at_price and self.compare_at_price > self.price:
            return round(((self.compare_at_price - self.price) / self.compare_at_price) * 100)
        return 0

class ProductImage(models.Model):
    """Product image gallery with caching support"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='product_images/')
    alt_text = models.CharField(max_length=125, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Product Image')
        verbose_name_plural = _('Product Images')
        ordering = ['order']
        unique_together = ('product', 'order')

    def __str__(self):
        return f"Image for {self.product.name}"

    def save(self, *args, **kwargs):
        if self.is_primary:
            self.__class__.objects.filter(
                product=self.product,
                is_primary=True
            ).update(is_primary=False)
        super().save(*args, **kwargs)
        # Clear product cache
        cache_key = PRODUCT_CACHE_KEY.format(id=self.product_id)
        cache.delete(cache_key)

class ProductVariant(models.Model):
    """Product variants with caching support"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants'
    )
    name = models.CharField(max_length=100)
    sku = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Product Variant')
        verbose_name_plural = _('Product Variants')
        unique_together = ('product', 'name')

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update variant cache
        cache_key = PRODUCT_VARIANT_CACHE_KEY.format(id=self.id)
        cache.set(cache_key, self, CACHE_TTL)
        # Clear product cache
        cache_key = PRODUCT_CACHE_KEY.format(id=self.product_id)
        cache.delete(cache_key)

    def delete(self, *args, **kwargs):
        # Clear caches
        cache_key = PRODUCT_VARIANT_CACHE_KEY.format(id=self.id)
        cache.delete(cache_key)
        cache_key = PRODUCT_CACHE_KEY.format(id=self.product_id)
        cache.delete(cache_key)
        super().delete(*args, **kwargs)

    @classmethod
    def get_cached(cls, variant_id):
        cache_key = PRODUCT_VARIANT_CACHE_KEY.format(id=variant_id)
        variant = cache.get(cache_key)
        if not variant:
            variant = cls.objects.select_related('product').get(id=variant_id)
            cache.set(cache_key, variant, CACHE_TTL)
        return variant

class ProductReview(models.Model):
    """Product reviews with caching support"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    user = models.ForeignKey(
        'Users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='reviews'
    )
    rating = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 6)],
        default=5
    )
    title = models.CharField(max_length=120)
    comment = models.TextField()
    vendor_response = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Product Review')
        verbose_name_plural = _('Product Reviews')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['user']),
            models.Index(fields=['rating']),
            models.Index(fields=['is_approved']),
        ]

    def __str__(self):
        return f"Review for {self.product.name} by {self.user.email if self.user else 'Anonymous'}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update review cache
        cache_key = PRODUCT_REVIEW_CACHE_KEY.format(id=self.id)
        cache.set(cache_key, self, CACHE_TTL)
        # Clear product cache to update rating
        cache_key = PRODUCT_CACHE_KEY.format(id=self.product_id)
        cache.delete(cache_key)

    def delete(self, *args, **kwargs):
        # Clear caches
        cache_key = PRODUCT_REVIEW_CACHE_KEY.format(id=self.id)
        cache.delete(cache_key)
        cache_key = PRODUCT_CACHE_KEY.format(id=self.product_id)
        cache.delete(cache_key)
        super().delete(*args, **kwargs)

    @classmethod
    def get_cached(cls, review_id):
        cache_key = PRODUCT_REVIEW_CACHE_KEY.format(id=review_id)
        review = cache.get(cache_key)
        if not review:
            review = cls.objects.select_related('product', 'user').get(id=review_id)
            cache.set(cache_key, review, CACHE_TTL)
        return review

class ProductQuestion(models.Model):
    """Product questions with caching support"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    user = models.ForeignKey(
        'Users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='questions'
    )
    question = models.TextField()
    answer = models.TextField(blank=True)
    answered_by = models.ForeignKey(
        'Users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='answered_questions'
    )
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Product Question')
        verbose_name_plural = _('Product Questions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['user']),
            models.Index(fields=['is_approved']),
        ]

    def __str__(self):
        return f"Question about {self.product.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update question cache
        cache_key = PRODUCT_QUESTION_CACHE_KEY.format(id=self.id)
        cache.set(cache_key, self, CACHE_TTL)

    def delete(self, *args, **kwargs):
        # Clear cache
        cache_key = PRODUCT_QUESTION_CACHE_KEY.format(id=self.id)
        cache.delete(cache_key)
        super().delete(*args, **kwargs)

    @classmethod
    def get_cached(cls, question_id):
        cache_key = PRODUCT_QUESTION_CACHE_KEY.format(id=question_id)
        question = cache.get(cache_key)
        if not question:
            question = cls.objects.select_related('product', 'user').get(id=question_id)
            cache.set(cache_key, question, CACHE_TTL)
        return question