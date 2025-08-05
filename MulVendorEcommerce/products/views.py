from rest_framework import viewsets, permissions, filters, status
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, signals
from django.core.cache import cache
from django.dispatch import receiver
import redis
from django.conf import settings
import math

from .models import Category, Product, ProductImage, ProductVariant, ProductReview, ProductQuestion
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    ProductListSerializer,
    ProductAdminSerializer,
    ProductImageSerializer,
    ProductVariantSerializer,
    ProductReviewSerializer,
    ProductQuestionSerializer
)   
from Users.serializers import UserSerializer, VendorProfileSerializer
from Users.models import Vendor
from Users.permissions import IsVendorOwner, IsVendorEmployee, IsSuperAdmin, IsProfileOwner

# Initialize Redis connection
redis_client = redis.StrictRedis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
    
)

# Cache timeout settings (in seconds)
PRODUCT_CACHE_TIMEOUT = 60 * 15  # 15 minutes
PRODUCT_LIST_CACHE_TIMEOUT = 60 * 5  # 5 minutes
CATEGORY_CACHE_TIMEOUT = 60 * 60 * 24  # 24 hours
REVIEW_CACHE_TIMEOUT = 60 * 30  # 30 minutes
QUESTION_CACHE_TIMEOUT = 60 * 30  # 30 minutes


class GeoLocationHelper:
    """
    Helper class for geolocation calculations and operations
    """
    
    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points on Earth using Haversine formula.
        
        Args:
            lat1 (float): Latitude of point 1 in decimal degrees
            lon1 (float): Longitude of point 1 in decimal degrees
            lat2 (float): Latitude of point 2 in decimal degrees
            lon2 (float): Longitude of point 2 in decimal degrees
            
        Returns:
            float: Distance between the points in kilometers
        """
        # Convert decimal degrees to radians 
        lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

        # Haversine formula 
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a)) 
        r = 6371  # Radius of earth in kilometers
        return c * r

    @staticmethod
    def get_nearby_vendors(latitude: float, longitude: float, radius_km: float) -> list:
        """
        Find vendors within a specified radius of given coordinates.
        
        Args:
            latitude (float): Center point latitude
            longitude (float): Center point longitude
            radius_km (float): Search radius in kilometers
            
        Returns:
            list: List of VendorProfile objects sorted by distance (nearest first)
        """
        vendors = Vendor.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False,
            is_active=True,
            verification_status=Vendor.VerificationStatus.VERIFIED
        )
        
        nearby_vendors = []
        
        for vendor in vendors:
            distance = GeoLocationHelper.haversine_distance(
                latitude, longitude,
                vendor.latitude, vendor.longitude
            )
            if distance <= radius_km:
                vendor.distance = distance
                nearby_vendors.append(vendor)
        
        return sorted(nearby_vendors, key=lambda x: x.distance)


class CacheSignalHandlers:
    """
    Class containing signal handlers for cache invalidation
    """
    
    @staticmethod
    @receiver(signals.post_save, sender=Product)
    @receiver(signals.post_delete, sender=Product)
    def invalidate_product_cache(sender, instance, **kwargs):
        """Invalidate cache when products are updated or deleted"""
        keys_to_delete = [
            f'product_{instance.id}',
            f'product_similar_{instance.id}',
            f'products_vendor_{instance.vendor_id}',
            'featured_products',
            'popular_products',
            'all_active_products'
        ]
        cache.delete_many(keys_to_delete)

    @staticmethod
    @receiver(signals.post_save, sender=ProductImage)
    @receiver(signals.post_delete, sender=ProductImage)
    def invalidate_product_image_cache(sender, instance, **kwargs):
        """Invalidate cache when product images are updated"""
        cache.delete(f'product_{instance.product_id}_images')
        cache.delete(f'product_image_{instance.id}')

    @staticmethod
    @receiver(signals.post_save, sender=ProductVariant)
    @receiver(signals.post_delete, sender=ProductVariant)
    def invalidate_product_variant_cache(sender, instance, **kwargs):
        """Invalidate cache when product variants are updated"""
        cache.delete(f'product_{instance.product_id}_variants')
        cache.delete(f'product_variant_{instance.id}')

    @staticmethod
    @receiver(signals.post_save, sender=Category)
    @receiver(signals.post_delete, sender=Category)
    def invalidate_category_cache(sender, instance, **kwargs):
        """Invalidate cache when categories are updated"""
        cache.delete_many([
            f'category_{instance.slug}',
            'all_categories',
            f'category_{instance.slug}_products'
        ])

    @staticmethod
    @receiver(signals.post_save, sender=ProductReview)
    @receiver(signals.post_delete, sender=ProductReview)
    def invalidate_review_cache(sender, instance, **kwargs):
        """Invalidate cache when reviews are updated"""
        cache.delete_many([
            f'product_{instance.product_id}_reviews',
            f'review_{instance.id}',
            f'user_{instance.user_id}_reviews'
        ])

    @staticmethod
    @receiver(signals.post_save, sender=ProductQuestion)
    @receiver(signals.post_delete, sender=ProductQuestion)
    def invalidate_question_cache(sender, instance, **kwargs):
        """Invalidate cache when questions are updated"""
        cache.delete_many([
            f'product_{instance.product_id}_questions',
            f'question_{instance.id}',
            f'user_{instance.user_id}_questions'
        ])


class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing product categories with Redis caching.
    
    Provides CRUD operations for product categories with hierarchical structure support.
    Includes caching for improved performance and search functionality.
    
    Permissions:
    - Read operations: Open to all (authenticated or not)
    - Write operations: Restricted to superadmins only
    """
    
    queryset = Category.objects.filter(parent_category=None).prefetch_related('subcategories')
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    def get_permissions(self):
        """Override permissions for write operations"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsSuperAdmin()]
        return super().get_permissions()

    def get_queryset(self):
        """Retrieve categories with caching"""
        cache_key = 'all_categories'
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return cached_data
            
        queryset = super().get_queryset()
        cache.set(cache_key, queryset, timeout=CATEGORY_CACHE_TIMEOUT)
        return queryset

    def retrieve(self, request, *args, **kwargs):
        """Retrieve single category with caching"""
        cache_key = f'category_{kwargs["slug"]}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
            
        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=CATEGORY_CACHE_TIMEOUT)
        return response

    @action(detail=True, methods=['get'])
    def products(self, request, slug=None):
        """
        Get all active, approved products for a specific category.
        
        Returns:
        - category: The category details
        - products: List of products in this category
        - count: Number of products
        """
        cache_key = f'category_{slug}_products'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
            
        category = self.get_object()
        products = Product.objects.filter(
            category=category,
            is_active=True,
            status=Product.Status.APPROVED
        ).select_related('vendor', 'category').prefetch_related('images', 'variants')
        
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        response_data = {
            'category': self.get_serializer(category).data,
            'products': serializer.data,
            'count': len(serializer.data)
        }
        cache.set(cache_key, response_data, timeout=PRODUCT_LIST_CACHE_TIMEOUT)
        return Response(response_data)


class ProductViewSet(viewsets.ModelViewSet):
    """
    API endpoint for product management with Redis caching.
    
    Provides comprehensive product operations including:
    - CRUD operations with proper permissions
    - Advanced filtering, searching and ordering
    - Location-based product discovery
    - Featured and popular products
    - Vendor-specific product management
    
    Permissions:
    - Read operations: Open to all
    - Create: Vendor employees
    - Update/Delete: Vendor owners or superadmins
    """
    
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'category': ['exact', 'in'],
        'vendor': ['exact'],
        'is_active': ['exact'],
        'status': ['exact'],
        'price': ['gte', 'lte', 'range'],
        'created_at': ['gte', 'lte']
    }
    search_fields = ['name', 'description', 'short_description', 'sku', 'vendor__user__business_name']
    ordering_fields = ['price', 'created_at', 'rating', 'view_count', 'updated_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'list':
            return ProductListSerializer
        elif self.request.user.is_superuser and self.action in ['retrieve', 'update', 'partial_update']:
            return ProductAdminSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        """Dynamically assign permissions based on action"""
        if self.action in ['create', 'toggle_activation']:
            return [IsVendorEmployee()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [(IsVendorOwner | IsSuperAdmin)()]
        return [permissions.IsAuthenticatedOrReadOnly()]

    def get_queryset(self):
        """Retrieve products with caching and proper visibility filters"""
        user = self.request.user
        cache_key = self._generate_cache_key(user)
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return cached_data
            
        queryset = self._build_base_queryset()
        queryset = self._apply_user_filters(queryset, user)
        
        cache.set(cache_key, queryset, timeout=PRODUCT_LIST_CACHE_TIMEOUT)
        return queryset

    def _generate_cache_key(self, user) -> str:
        """
        Generate dynamic cache key based on user and request parameters
        
        Args:
            user: The current user making the request
            
        Returns:
            str: Generated cache key
        """
        base_key = 'products_'
        params = self.request.query_params.dict()
        
        if user.is_authenticated:
            if user.is_superuser:
                base_key += 'admin_'
            elif hasattr(user, 'vendor'):
                base_key += f'vendor_{user.vendor.id}_'
            elif hasattr(user, 'vendor_employee'):
                base_key += f'vendor_{user.vendor_employee.vendor.id}_'
        
        return base_key + '_'.join(f"{k}_{v}" for k, v in sorted(params.items()))

    def _build_base_queryset(self):
        """Build the base queryset with related data"""
        return Product.objects.select_related(
            'vendor', 'vendor__user', 'category', 'created_by', 'updated_by'
        ).prefetch_related(
            'images', 'variants', 'reviews', 'questions'
        )

    def _apply_user_filters(self, queryset, user):
        """
        Apply user-specific visibility filters to the queryset
        
        Args:
            queryset: The base queryset to filter
            user: The current user making the request
            
        Returns:
            QuerySet: Filtered queryset based on user permissions
        """
        if user.is_authenticated:
            if user.is_superuser:
                return queryset
            if hasattr(user, 'vendor'):
                return queryset.filter(vendor=user.vendor)
            if hasattr(user, 'vendor_employee'):
                return queryset.filter(vendor=user.vendor_employee.vendor)
        
        return queryset.filter(
            is_active=True, 
            status=Product.Status.APPROVED,
            vendor__verification_status=Vendor.VerificationStatus.VERIFIED
        )

    def retrieve(self, request, *args, **kwargs):
        """Retrieve single product with caching"""
        cache_key = f'product_{kwargs["pk"]}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
            
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        # Increment view count for non-owners
        if not (request.user.is_superuser or 
                (hasattr(request.user, 'vendor') and request.user.vendor == instance.vendor) or
                (hasattr(request.user, 'vendor_employee') and request.user.vendor_employee.vendor == instance.vendor)):
            instance.view_count += 1
            instance.save()
        
        response = Response(serializer.data)
        cache.set(cache_key, serializer.data, timeout=PRODUCT_CACHE_TIMEOUT)
        return response

    def perform_create(self, serializer):
        """Set the vendor and created_by/updated_by when creating a new product"""
        user = self.request.user
        if hasattr(user, 'vendor'):
            serializer.save(
                vendor=user.vendor,
                created_by=user,
                updated_by=user
            )
        elif hasattr(user, 'vendor_employee'):
            serializer.save(
                vendor=user.vendor_employee.vendor,
                created_by=user,
                updated_by=user
            )
        else:
            raise PermissionDenied("You don't have permission to create products.")

    def perform_update(self, serializer):
        """Set updated_by when updating a product"""
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsVendorOwner | IsSuperAdmin | IsVendorEmployee])
    def toggle_activation(self, request, pk=None):
        """
        Toggle product active status
        
        Returns:
        - status: 'success'
        - is_active: New activation status
        """
        product = self.get_object()
        product.is_active = not product.is_active
        if product.is_active and product.status != Product.Status.APPROVED:
            product.status = Product.Status.PENDING
        elif not product.is_active:
            product.status = Product.Status.INACTIVE
        product.updated_by = request.user
        product.save()
        return Response({'status': 'success', 'is_active': product.is_active})

    @action(detail=False, methods=['get'], permission_classes=[IsVendorOwner | IsVendorEmployee | IsSuperAdmin])
    def my_products(self, request):
        """
        Get all products for the current vendor/employee
        
        Returns:
        - count: Number of products
        - results: List of products
        """
        cache_key = f'vendor_{request.user.vendor.id}_products' if hasattr(request.user, 'vendor') else \
                   f'vendor_{request.user.vendor_employee.vendor.id}_products'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
            
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        response_data = {
            'count': len(serializer.data),
            'results': serializer.data
        }
        cache.set(cache_key, response_data, timeout=PRODUCT_LIST_CACHE_TIMEOUT)
        return Response(response_data)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """
        Get featured products (max 12)
        
        Returns:
        - count: Number of featured products
        - results: List of featured products
        """
        cache_key = 'featured_products'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
            
        featured = self.get_queryset().filter(is_featured=True, is_active=True, status=Product.Status.APPROVED)[:12]
        serializer = ProductListSerializer(featured, many=True, context={'request': request})
        response_data = {
            'count': len(serializer.data),
            'results': serializer.data
        }
        cache.set(cache_key, response_data, timeout=PRODUCT_LIST_CACHE_TIMEOUT)
        return Response(response_data)

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """
        Get popular products (most viewed, max 12)
        
        Returns:
        - count: Number of popular products
        - results: List of popular products
        """
        cache_key = 'popular_products'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
            
        popular = self.get_queryset().filter(is_active=True, status=Product.Status.APPROVED).order_by('-view_count')[:12]
        serializer = ProductListSerializer(popular, many=True, context={'request': request})
        response_data = {
            'count': len(serializer.data),
            'results': serializer.data
        }
        cache.set(cache_key, response_data, timeout=PRODUCT_LIST_CACHE_TIMEOUT)
        return Response(response_data)

    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """
        Get products from nearby vendors within specified radius
        
        Parameters:
        - lat: Latitude of center point (required)
        - lng: Longitude of center point (required)
        - radius: Search radius in km (default: 50)
        
        Returns:
        List of products with distance information
        """
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius = float(request.query_params.get('radius', 50))  # Default 50km radius
        
        if not lat or not lng:
            return Response(
                {'error': 'Latitude and longitude parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            lat = float(lat)
            lng = float(lng)
        except ValueError:
            return Response(
                {'error': 'Invalid latitude or longitude values'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate cache key
        cache_key = f'nearby_products_{lat}_{lng}_{radius}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        # Get nearby vendors
        nearby_vendors = GeoLocationHelper.get_nearby_vendors(lat, lng, radius)
        vendor_ids = [v.id for v in nearby_vendors]
        
        # Get products from these vendors
        products = self.get_queryset().filter(
            vendor_id__in=vendor_ids,
            is_active=True,
            status=Product.Status.APPROVED
        )
        
        # Add distance information to each product
        product_data = []
        for product in products:
            vendor = product.vendor
            distance = GeoLocationHelper.haversine_distance(
                lat, lng,
                vendor.latitude, vendor.longitude
            )
            product_data.append({
                'product': product,
                'distance': distance
            })
        
        # Sort by distance
        product_data.sort(key=lambda x: x['distance'])
        
        # Serialize the results
        serializer = ProductListSerializer(
            [item['product'] for item in product_data],
            many=True,
            context={'request': request}
        )
        
        # Add distance to each product in response
        response_data = []
        for i, product in enumerate(serializer.data):
            response_data.append({
                **product,
                'distance': product_data[i]['distance']
            })
        
        cache.set(cache_key, response_data, timeout=PRODUCT_LIST_CACHE_TIMEOUT)
        return Response(response_data)

    @action(detail=True, methods=['get'])
    def similar_nearby(self, request, pk=None):
        """
        Get similar products (same category) from nearby vendors
        
        Parameters:
        - lat: Latitude of center point (required)
        - lng: Longitude of center point (required)
        - radius: Search radius in km (default: 50)
        
        Returns:
        List of similar products with distance information
        """
        product = self.get_object()
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius = float(request.query_params.get('radius', 50))  # Default 50km radius
        
        if not lat or not lng:
            return Response(
                {'error': 'Latitude and longitude parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            lat = float(lat)
            lng = float(lng)
        except ValueError:
            return Response(
                {'error': 'Invalid latitude or longitude values'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate cache key
        cache_key = f'similar_nearby_{product.id}_{lat}_{lng}_{radius}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        # Get nearby vendors
        nearby_vendors = GeoLocationHelper.get_nearby_vendors(lat, lng, radius)
        vendor_ids = [v.id for v in nearby_vendors]
        
        # Get similar products (same category) from these vendors
        similar_products = self.get_queryset().filter(
            vendor_id__in=vendor_ids,
            category=product.category,
            is_active=True,
            status=Product.Status.APPROVED
        ).exclude(id=product.id)
        
        # Add distance information to each product
        product_data = []
        for p in similar_products:
            vendor = p.vendor
            distance = GeoLocationHelper.haversine_distance(
                lat, lng,
                vendor.latitude, vendor.longitude
            )
            product_data.append({
                'product': p,
                'distance': distance
            })
        
        # Sort by distance
        product_data.sort(key=lambda x: x['distance'])
        
        # Serialize the results
        serializer = ProductListSerializer(
            [item['product'] for item in product_data],
            many=True,
            context={'request': request}
        )
        
        # Add distance to each product in response
        response_data = []
        for i, product in enumerate(serializer.data):
            response_data.append({
                **product,
                'distance': product_data[i]['distance']
            })
        
        cache.set(cache_key, response_data, timeout=PRODUCT_CACHE_TIMEOUT)
        return Response(response_data)


class ProductImageViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing product images.
    
    Provides CRUD operations for product images with proper permissions
    and caching for improved performance.
    
    Permissions:
    - Read: Open to all
    - Write: Vendor owners/employees or superadmins
    """
    
    serializer_class = ProductImageSerializer
    queryset = ProductImage.objects.select_related('product__vendor', 'uploaded_by')

    def get_permissions(self):
        """Dynamically assign permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [(IsVendorOwner|IsVendorEmployee | IsSuperAdmin)()]
        return [permissions.IsAuthenticatedOrReadOnly()]

    def get_queryset(self):
        """Filter images based on user permissions"""
        user = self.request.user
        if user.is_superuser:
            return self.queryset.all()
        
        if hasattr(user, 'vendor'):
            return self.queryset.filter(product__vendor=user.vendor)
        if hasattr(user, 'vendor_employee'):
            return self.queryset.filter(product__vendor=user.vendor_employee.vendor)
        
        # For non-vendor users, only show images for active, approved products
        return self.queryset.filter(
            product__is_active=True,
            product__status=Product.Status.APPROVED
        )

    def retrieve(self, request, *args, **kwargs):
        """Retrieve single image with caching"""
        cache_key = f'product_image_{kwargs["pk"]}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
            
        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=PRODUCT_CACHE_TIMEOUT)
        return response

    @action(detail=False, methods=['get'])
    def product_images(self, request):
        """
        Get all images for a specific product
        
        Parameters:
        - product_id: ID of the product (required)
        
        Returns:
        List of product images
        """
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response(
                {'error': 'product_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cache_key = f'product_{product_id}_images'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
            
        images = self.get_queryset().filter(product_id=product_id)
        serializer = self.get_serializer(images, many=True)
        cache.set(cache_key, serializer.data, timeout=PRODUCT_CACHE_TIMEOUT)
        return Response(serializer.data)


class ProductVariantViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing product variants.
    
    Provides CRUD operations for product variants with proper permissions
    and caching for improved performance.
    
    Permissions:
    - Read: Open to all
    - Write: Vendor owners/employees or superadmins
    """
    
    serializer_class = ProductVariantSerializer
    queryset = ProductVariant.objects.select_related('product__vendor', 'created_by', 'updated_by')

    def get_permissions(self):
        """Dynamically assign permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [(IsVendorOwner|IsVendorEmployee | IsSuperAdmin)()]
        return [permissions.IsAuthenticatedOrReadOnly()]

    def get_queryset(self):
        """Filter variants based on user permissions"""
        user = self.request.user
        if user.is_superuser:
            return self.queryset.all()
        
        if hasattr(user, 'vendor'):
            return self.queryset.filter(product__vendor=user.vendor)
        if hasattr(user, 'vendor_employee'):
            return self.queryset.filter(product__vendor=user.vendor_employee.vendor)
        
        # For non-vendor users, only show variants for active, approved products
        return self.queryset.filter(
            product__is_active=True,
            product__status=Product.Status.APPROVED
        )

    def retrieve(self, request, *args, **kwargs):
        """Retrieve single variant with caching"""
        cache_key = f'product_variant_{kwargs["pk"]}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
            
        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=PRODUCT_CACHE_TIMEOUT)
        return response

    @action(detail=False, methods=['get'])
    def product_variants(self, request):
        """
        Get all variants for a specific product
        
        Parameters:
        - product_id: ID of the product (required)
        
        Returns:
        List of product variants
        """
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response(
                {'error': 'product_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cache_key = f'product_{product_id}_variants'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
            
        variants = self.get_queryset().filter(product_id=product_id)
        serializer = self.get_serializer(variants, many=True)
        cache.set(cache_key, serializer.data, timeout=PRODUCT_CACHE_TIMEOUT)
        return Response(serializer.data)


class ProductReviewViewSet(viewsets.ModelViewSet):
    """
    API endpoint for product reviews.
    
    Provides CRUD operations for product reviews with proper permissions
    and caching for improved performance.
    
    Permissions:
    - Create: Authenticated users
    - Update/Delete: Review owner or superadmin
    - Respond: Vendor owner
    - Read: Open to all (approved reviews only for non-owners)
    """
    
    serializer_class = ProductReviewSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['product', 'user', 'rating', 'is_approved']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']

    def get_permissions(self):
        """Dynamically assign permissions based on action"""
        if self.action == 'create':
            return [permissions.IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsProfileOwner() | IsSuperAdmin()]
        elif self.action == 'respond':
            return [IsVendorOwner()]
        return [permissions.IsAuthenticatedOrReadOnly()]

    def get_queryset(self):
        """Retrieve reviews with caching and proper visibility filters"""
        cache_key = self._generate_reviews_cache_key()
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return cached_data
            
        queryset = self._build_base_queryset()
        cache.set(cache_key, queryset, timeout=REVIEW_CACHE_TIMEOUT)
        return queryset

    def _generate_reviews_cache_key(self) -> str:
        """
        Generate dynamic cache key based on request parameters and user
        
        Returns:
            str: Generated cache key
        """
        base_key = 'reviews_'
        params = self.request.query_params.dict()
        user = self.request.user
        
        if user.is_authenticated:
            if user.is_superuser:
                base_key += 'admin_'
            elif hasattr(user, 'vendor'):
                base_key += f'vendor_{user.vendor.id}_'
            elif hasattr(user, 'vendor_employee'):
                base_key += f'vendor_{user.vendor_employee.vendor.id}_'
            else:
                base_key += f'user_{user.id}_'
        
        return base_key + '_'.join(f"{k}_{v}" for k, v in sorted(params.items()))

    def _build_base_queryset(self):
        """Build the base queryset with proper filters"""
        user = self.request.user
        queryset = ProductReview.objects.select_related('user', 'product', 'product__vendor')

        if user.is_authenticated:
            if user.is_superuser:
                return queryset
            if hasattr(user, 'vendor') or hasattr(user, 'vendor_employee'):
                vendor = user.vendor if hasattr(user, 'vendor') else user.vendor_employee.vendor
                return queryset.filter(product__vendor=vendor)
            return queryset.filter(Q(user=user) | Q(is_approved=True))
        
        return queryset.filter(is_approved=True)

    def retrieve(self, request, *args, **kwargs):
        """Retrieve single review with caching"""
        cache_key = f'review_{kwargs["pk"]}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
            
        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=REVIEW_CACHE_TIMEOUT)
        return response

    def perform_create(self, serializer):
        """Set the user when creating a new review"""
        serializer.save(user=self.request.user, is_approved=False)

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """
        Vendor response to a review
        
        Parameters:
        - response: The vendor's response text (required)
        
        Returns:
        The updated review with vendor response
        """
        review = self.get_object()
        response_text = request.data.get('response', '').strip()
        
        if not response_text:
            return Response(
                {'detail': 'Response text is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        review.vendor_response = response_text
        review.save()
        
        # Invalidate relevant caches
        cache.delete(f'review_{review.id}')
        cache.delete(f'product_{review.product_id}_reviews')
        return Response(self.get_serializer(review).data)

    @action(detail=True, methods=['post'], permission_classes=[IsVendorOwner | IsSuperAdmin])
    def approve(self, request, pk=None):
        """
        Approve a review (vendor owner or admin only)
        
        Returns:
        The updated review with is_approved=True
        """
        review = self.get_object()
        review.is_approved = True
        review.save()
        
        # Invalidate relevant caches
        cache.delete(f'review_{review.id}')
        cache.delete(f'product_{review.product_id}_reviews')
        return Response(self.get_serializer(review).data)


class ProductQuestionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for product questions.
    
    Provides CRUD operations for product questions with proper permissions
    and caching for improved performance.
    
    Permissions:
    - Create: Authenticated users
    - Update/Delete: Question owner or superadmin
    - Answer: Vendor owner/employee
    - Read: Open to all (approved questions only for non-owners)
    """
    
    serializer_class = ProductQuestionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'user', 'is_approved']

    def get_permissions(self):
        """Dynamically assign permissions based on action"""
        if self.action == 'create':
            return [permissions.IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsProfileOwner() | IsSuperAdmin()]
        elif self.action == 'answer':
            return [IsVendorOwner() | IsVendorEmployee()]
        return [permissions.IsAuthenticatedOrReadOnly()]

    def get_queryset(self):
        """Retrieve questions with caching and proper visibility filters"""
        cache_key = self._generate_questions_cache_key()
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return cached_data
            
        queryset = self._build_base_queryset()
        cache.set(cache_key, queryset, timeout=QUESTION_CACHE_TIMEOUT)
        return queryset

    def _generate_questions_cache_key(self) -> str:
        """
        Generate dynamic cache key based on request parameters and user
        
        Returns:
            str: Generated cache key
        """
        base_key = 'questions_'
        params = self.request.query_params.dict()
        user = self.request.user
        
        if user.is_authenticated:
            if user.is_superuser:
                base_key += 'admin_'
            elif hasattr(user, 'vendor'):
                base_key += f'vendor_{user.vendor.id}_'
            elif hasattr(user, 'vendor_employee'):
                base_key += f'vendor_{user.vendor_employee.vendor.id}_'
            else:
                base_key += f'user_{user.id}_'
        
        return base_key + '_'.join(f"{k}_{v}" for k, v in sorted(params.items()))

    def _build_base_queryset(self):
        """Build the base queryset with proper filters"""
        user = self.request.user
        queryset = ProductQuestion.objects.select_related('user', 'product', 'answered_by', 'product__vendor')

        if user.is_authenticated:
            if user.is_superuser:
                return queryset
            if hasattr(user, 'vendor') or hasattr(user, 'vendor_employee'):
                vendor = user.vendor if hasattr(user, 'vendor') else user.vendor_employee.vendor
                return queryset.filter(product__vendor=vendor)
            return queryset.filter(Q(user=user) | Q(is_approved=True))
        
        return queryset.filter(is_approved=True)

    def retrieve(self, request, *args, **kwargs):
        """Retrieve single question with caching"""
        cache_key = f'question_{kwargs["pk"]}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
            
        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=QUESTION_CACHE_TIMEOUT)
        return response

    def perform_create(self, serializer):
        """Set the user when creating a new question"""
        serializer.save(user=self.request.user, is_approved=False)

    @action(detail=True, methods=['post'])
    def answer(self, request, pk=None):
        """
        Vendor response to a question
        
        Parameters:
        - answer: The vendor's answer text (required)
        
        Returns:
        The updated question with vendor answer
        """
        question = self.get_object()
        answer_text = request.data.get('answer', '').strip()
        
        if not answer_text:
            return Response(
                {'detail': 'Answer text is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        question.answer = answer_text
        question.answered_by = request.user
        question.save()
        
        # Invalidate relevant caches
        cache.delete(f'question_{question.id}')
        cache.delete(f'product_{question.product_id}_questions')
        return Response(self.get_serializer(question).data)

    @action(detail=True, methods=['post'], permission_classes=[IsVendorOwner | IsSuperAdmin])
    def approve(self, request, pk=None):
        """
        Approve a question (vendor owner or admin only)
        
        Returns:
        The updated question with is_approved=True
        """
        question = self.get_object()
        question.is_approved = True
        question.save()
        
        # Invalidate relevant caches
        cache.delete(f'question_{question.id}')
        cache.delete(f'product_{question.product_id}_questions')
        return Response(self.get_serializer(question).data)


class VendorLocationViewSet(viewsets.ViewSet):
    """
    API endpoint for vendor location operations.
    
    Provides geolocation-based functionality for vendors including:
    - Finding vendors within a radius
    - Getting vendor coordinates
    """
    
    @action(detail=False, methods=['get'])
    def get_vendors_within_radius(self, request):
        """
        Get vendors within a specified radius using latitude/longitude
        
        Parameters:
        - lat: Latitude of center point (required)
        - lng: Longitude of center point (required)
        - radius: Search radius in km (default: 50)
        
        Returns:
        List of vendors sorted by distance (nearest first)
        """
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius = float(request.query_params.get('radius', 50))  # Default 50km
        
        if not lat or not lng:
            return Response(
                {'error': 'Latitude and longitude parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            vendors = Vendor.objects.filter(
                latitude__isnull=False,
                longitude__isnull=False,
                is_active=True,
                verification_status=Vendor.VerificationStatus.VERIFIED
            )
            
            nearby_vendors = GeoLocationHelper.get_nearby_vendors(float(lat), float(lng), radius)
            
            serializer = VendorProfileSerializer(nearby_vendors, many=True)
            return Response(serializer.data)
            
        except ValueError:
            return Response(
                {'error': 'Invalid latitude, longitude or radius values'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def get_vendor_coordinates(self, request, pk=None):
        """
        Get coordinates for a specific vendor
        
        Parameters:
        - pk: Vendor ID
        
        Returns:
        - latitude: Vendor's latitude
        - longitude: Vendor's longitude
        """
        try:
            vendor = Vendor.objects.get(id=pk)
            return Response({
                'latitude': vendor.latitude,
                'longitude': vendor.longitude
            })
        except Vendor.DoesNotExist:
            return Response(
                {'error': 'Vendor not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class CacheManagementView(APIView):
    """
    API endpoint for managing cache.
    
    Provides operations to clear specific cache segments.
    Restricted to superadmins only.
    """
    
    permission_classes = [IsSuperAdmin]

    def post(self, request):
        """
        Clear specific cache segments
        
        Parameters:
        - action: Cache segment to clear (required)
          Options: clear_all, clear_products, clear_categories, 
                  clear_reviews, clear_questions
        
        Returns:
        Status message
        """
        action = request.data.get('action')
        
        if action == 'clear_all':
            cache.clear()
            return Response({'status': 'All cache cleared'})
        
        elif action == 'clear_products':
            cache.delete_pattern('product_*')
            cache.delete_pattern('products_*')
            return Response({'status': 'Product cache cleared'})
        
        elif action == 'clear_categories':
            cache.delete_pattern('category_*')
            return Response({'status': 'Category cache cleared'})
        
        elif action == 'clear_reviews':
            cache.delete_pattern('review_*')
            return Response({'status': 'Review cache cleared'})
        
        elif action == 'clear_questions':
            cache.delete_pattern('question_*')
            return Response({'status': 'Question cache cleared'})
        
        return Response(
            {'error': 'Invalid action specified'},
            status=status.HTTP_400_BAD_REQUEST
        )