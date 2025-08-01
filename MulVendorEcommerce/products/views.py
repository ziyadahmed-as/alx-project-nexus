from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import PermissionDenied

from .models import Category, Product, ProductImage, ProductReview, ProductQuestion
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    ProductImageSerializer,
    ProductReviewSerializer,
    ProductQuestionSerializer
)
from Users.permissions import IsVendorOwner, IsProfileOwner, IsSuperAdmin
from Users.models import VendorEmployee


# ------------------ CATEGORY VIEWSET ------------------ #
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.filter(parent_category=None)
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'


# ------------------ PRODUCT VIEWSET ------------------ #
# This viewset handles product management for vendors and their employees.
# It allows vendors to create, update, and delete their products,
# and provides read access to all users.
class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'vendor', 'is_active']
    search_fields = ['name', 'description', 'sku']
    ordering_fields = ['price', 'created_at']

    def get_queryset(self):
        user = self.request.user

        if user.is_authenticated:
            if user.is_superuser:
                return Product.objects.all()
            elif hasattr(user, 'vendor'):
                return Product.objects.filter(vendor=user.vendor)
            elif hasattr(user, 'vendoremployee'):
                return Product.objects.filter(vendor=user.vendoremployee.vendor)

        return Product.objects.filter(is_active=True, is_approved=True)

    def perform_create(self, serializer):
        user = self.request.user

        if hasattr(user, 'vendor'):
            vendor = user.vendor
        elif hasattr(user, 'vendoremployee'):
            vendor = user.vendoremployee.vendor
        else:
            raise PermissionDenied("Only vendors or their employees can create products.")

        serializer.save(vendor=vendor)

    def perform_update(self, serializer):
        product = self.get_object()
        user = self.request.user

        if user.is_superuser:
            serializer.save()
        elif hasattr(user, 'vendor') and product.vendor == user.vendor:
            serializer.save()
        elif hasattr(user, 'vendoremployee') and product.vendor == user.vendoremployee.vendor:
            serializer.save()
        else:
            raise PermissionDenied("You do not have permission to update this product.")

    def perform_destroy(self, instance):
        user = self.request.user

        if user.is_superuser:
            instance.delete()
        elif hasattr(user, 'vendor') and instance.vendor == user.vendor:
            instance.delete()
        elif hasattr(user, 'vendoremployee') and instance.vendor == user.vendoremployee.vendor:
            instance.delete()
        else:
            raise PermissionDenied("You do not have permission to delete this product.")

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def upload_image(self, request, pk=None):
        product = self.get_object()
        user = request.user
        serializer = ProductImageSerializer(data=request.data)

        if serializer.is_valid():
            if user.is_superuser or (
                hasattr(user, 'vendor') and product.vendor == user.vendor
            ) or (
                hasattr(user, 'vendoremployee') and product.vendor == user.vendoremployee.vendor
            ):
                serializer.save(product=product)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ------------------ PRODUCT IMAGE VIEWSET ------------------ #
class ProductImageViewSet(viewsets.ModelViewSet):
    serializer_class = ProductImageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return ProductImage.objects.all()
        elif hasattr(user, 'vendor'):
            return ProductImage.objects.filter(product__vendor=user.vendor)
        elif hasattr(user, 'vendoremployee'):
            return ProductImage.objects.filter(product__vendor=user.vendoremployee.vendor)

        return ProductImage.objects.none()

    def perform_create(self, serializer):
        product = serializer.validated_data.get("product")
        user = self.request.user

        if user.is_superuser or (
            hasattr(user, 'vendor') and product.vendor == user.vendor
        ) or (
            hasattr(user, 'vendoremployee') and product.vendor == user.vendoremployee.vendor
        ):
            serializer.save()
        else:
            raise PermissionDenied("You can only upload images to your own products.")


# ------------------ PRODUCT REVIEW VIEWSET ------------------ #
class ProductReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ProductReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return ProductReview.objects.all()
        return ProductReview.objects.filter(is_approved=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsProfileOwner() | IsSuperAdmin()]
        return super().get_permissions()


# ------------------ PRODUCT QUESTION VIEWSET ------------------ #
class ProductQuestionViewSet(viewsets.ModelViewSet):
    serializer_class = ProductQuestionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return ProductQuestion.objects.all()
        return ProductQuestion.objects.filter(is_approved=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsProfileOwner() | IsSuperAdmin()]
        return super().get_permissions()
