from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.contrib.gis.geos import Point
from rest_framework.exceptions import PermissionDenied

from .models import Category, Product, ProductImage, ProductReview, ProductQuestion
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    ProductImageSerializer,
    ProductReviewSerializer,
    ProductQuestionSerializer
)
from Users.permissions import (
    IsSuperAdmin,
    IsVendorOrEmployee,
    IsProfileOwner,
    IsVendorEmployee
)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing product categories.
    - All users can view categories
    - Only superadmins can create/update/delete categories
    """
    queryset = Category.objects.filter(parent_category=None).prefetch_related('subcategories')
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsSuperAdmin()]
        return super().get_permissions()


class ProductViewSet(viewsets.ModelViewSet):
    """
    API endpoint for product management in multivendor marketplace.
    - Vendors can manage their own products
    - Vendor employees can manage products based on permissions
    - Customers can view active products
    - Admins have full access
    - Supports location-based product recommendations
    """
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'category': ['exact', 'in'],
        'vendor': ['exact'],
        'is_active': ['exact'],
        'is_approved': ['exact'],
        'price': ['gte', 'lte', 'range'],
        'created_at': ['gte', 'lte']
    }
    search_fields = ['name', 'description', 'sku', 'vendor__business_name']
    ordering_fields = ['price', 'created_at', 'rating', 'popularity', 'distance']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['create', 'toggle_activation']:
            return [IsVendorOrEmployee()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [(IsVendorOrEmployee | IsSuperAdmin)()]
        return [permissions.IsAuthenticatedOrReadOnly()]

    def get_queryset(self):
        user = self.request.user
        queryset = Product.objects.select_related(
            'vendor', 'category'
        ).prefetch_related(
            'images', 'reviews', 'questions'
        )

        # Apply location filter if coordinates provided
        lat = self.request.query_params.get('lat')
        lng = self.request.query_params.get('lng')
        radius = self.request.query_params.get('radius', 50)  # Default 50km radius

        if lat and lng:
            try:
                point = Point(float(lng), float(lat), srid=4326)
                queryset = queryset.filter(
                    vendor__location__distance_lte=(point, D(km=float(radius))))
                queryset = queryset.annotate(
                    distance=Distance('vendor__location', point)
                )
            except (ValueError, TypeError):
                pass  # Ignore invalid coordinates

        if user.is_authenticated:
            if user.is_superuser:
                return queryset
            if hasattr(user, 'vendor'):
                return queryset.filter(vendor=user.vendor)
            if hasattr(user, 'vendor_employee'):
                return queryset.filter(vendor=user.vendor_employee.vendor)

        # Public access - only approved and active products
        return queryset.filter(
            is_active=True, 
            is_approved=True,
            vendor__is_approved=True
        )

    def perform_create(self, serializer):
        if hasattr(self.request.user, 'vendor'):
            serializer.save(vendor=self.request.user.vendor)
        elif hasattr(self.request.user, 'vendor_employee'):
            serializer.save(vendor=self.request.user.vendor_employee.vendor)
        else:
            raise PermissionDenied("You don't have permission to create products.")

    @action(detail=True, methods=['post'], permission_classes=[IsVendorOrEmployee])
    def toggle_activation(self, request, pk=None):
        """Toggle product active status (vendor/admin only)"""
        product = self.get_object()
        product.is_active = not product.is_active
        product.save()
        return Response({'status': 'success', 'is_active': product.is_active})

    @action(detail=False, methods=['get'], permission_classes=[IsVendorOrEmployee])
    def my_products(self, request):
        """Get all products for the current vendor/employee"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """
        Get products from nearby vendors based on user's location
        Parameters:
        - lat: Latitude (required)
        - lng: Longitude (required)
        - radius: Search radius in kilometers (default: 50)
        """
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius = request.query_params.get('radius', 50)

        if not lat or not lng:
            return Response(
                {'error': 'Latitude and longitude parameters are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            point = Point(float(lng), float(lat), srid=4326)
            queryset = self.filter_queryset(self.get_queryset())
            
            nearby_products = queryset.filter(
                vendor__location__distance_lte=(point, D(km=float(radius))),
                is_active=True,
                is_approved=True
            ).annotate(
                distance=Distance('vendor__location', point)
            ).order_by('distance')[:50]

            serializer = self.get_serializer(nearby_products, many=True)
            return Response({
                'count': len(serializer.data),
                'results': serializer.data,
                'location': {'lat': lat, 'lng': lng},
                'radius_km': radius
            })
        except (ValueError, TypeError) as e:
            return Response(
                {'error': 'Invalid location parameters.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def similar_nearby(self, request, pk=None):
        """
        Get similar products from nearby vendors
        Parameters:
        - lat: Latitude (required)
        - lng: Longitude (required)
        - radius: Search radius in kilometers (default: 50)
        """
        product = self.get_object()
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius = request.query_params.get('radius', 50)

        if not lat or not lng:
            return Response(
                {'error': 'Location coordinates are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            point = Point(float(lng), float(lat), srid=4326)
            queryset = self.filter_queryset(self.get_queryset())
            
            similar_products = queryset.filter(
                Q(category=product.category) | 
                Q(name__icontains=product.name.split()[0]),
                vendor__location__distance_lte=(point, D(km=float(radius))),
                is_active=True,
                is_approved=True
            ).exclude(
                pk=product.pk
            ).annotate(
                distance=Distance('vendor__location', point)
            ).order_by('distance')[:12]

            serializer = self.get_serializer(similar_products, many=True)
            return Response({
                'product': self.get_serializer(product).data,
                'similar_nearby': serializer.data,
                'location': {'lat': lat, 'lng': lng},
                'search_radius_km': radius
            })
        except (ValueError, TypeError) as e:
            return Response(
                {'error': 'Invalid location parameters.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class ProductImageViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing product images.
    - Vendor owners can manage images for their products
    - Vendor employees can manage images if permitted
    - Admins have full access
    """
    serializer_class = ProductImageSerializer
    queryset = ProductImage.objects.select_related('product__vendor')

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [(IsVendorOrEmployee | IsSuperAdmin)()]
        return [permissions.IsAuthenticatedOrReadOnly()]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return self.queryset.all()
        
        if hasattr(user, 'vendor'):
            return self.queryset.filter(product__vendor=user.vendor)
        if hasattr(user, 'vendor_employee'):
            return self.queryset.filter(product__vendor=user.vendor_employee.vendor)
        
        return self.queryset.none()

    def perform_create(self, serializer):
        product = serializer.validated_data.get('product')
        if hasattr(self.request.user, 'vendor'):
            if product.vendor != self.request.user.vendor:
                raise PermissionDenied("You can only upload images to your own products.")
        elif hasattr(self.request.user, 'vendor_employee'):
            if product.vendor != self.request.user.vendor_employee.vendor:
                raise PermissionDenied("You can only upload images to your vendor's products.")
        serializer.save()


class ProductReviewViewSet(viewsets.ModelViewSet):
    """
    API endpoint for product reviews.
    - Customers can create reviews for purchased products
    - All users can read approved reviews
    - Review owners can update/delete their reviews
    - Vendors can respond to reviews
    """
    serializer_class = ProductReviewSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['product', 'user', 'rating', 'is_approved']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsProfileOwner() | IsSuperAdmin()]
        elif self.action == 'respond':
            return [IsVendorOrEmployee()]
        return [permissions.IsAuthenticatedOrReadOnly()]

    def get_queryset(self):
        user = self.request.user
        queryset = ProductReview.objects.select_related('user', 'product')

        if user.is_authenticated:
            if user.is_superuser:
                return queryset
            if hasattr(user, 'vendor') or hasattr(user, 'vendor_employee'):
                vendor = user.vendor if hasattr(user, 'vendor') else user.vendor_employee.vendor
                return queryset.filter(product__vendor=vendor)
            return queryset.filter(Q(user=user) | Q(is_approved=True))
        
        return queryset.filter(is_approved=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """Vendor response to a review"""
        review = self.get_object()
        response_text = request.data.get('response', '').strip()
        
        if not response_text:
            return Response(
                {'detail': 'Response text is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        review.vendor_response = response_text
        review.save()
        return Response(self.get_serializer(review).data)


class ProductQuestionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for product questions and answers.
    - Customers can ask questions
    - Vendors/employees can answer questions
    - All users can read approved questions
    """
    serializer_class = ProductQuestionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'user', 'is_approved']

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsProfileOwner() | IsSuperAdmin()]
        elif self.action == 'answer':
            return [IsVendorOrEmployee()]
        return [permissions.IsAuthenticatedOrReadOnly()]

    def get_queryset(self):
        user = self.request.user
        queryset = ProductQuestion.objects.select_related('user', 'product')

        if user.is_authenticated:
            if user.is_superuser:
                return queryset
            if hasattr(user, 'vendor') or hasattr(user, 'vendor_employee'):
                vendor = user.vendor if hasattr(user, 'vendor') else user.vendor_employee.vendor
                return queryset.filter(product__vendor=vendor)
            return queryset.filter(Q(user=user) | Q(is_approved=True))
        
        return queryset.filter(is_approved=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def answer(self, request, pk=None):
        """Vendor response to a question"""
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
        return Response(self.get_serializer(question).data)