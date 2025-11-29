from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.core.cache import cache
from .models import Category, Product, ProductImage
from .serializers import CategorySerializer, ProductSerializer, ProductImageSerializer
from apps.vendors.permissions import IsVendor

class CategoryListView(generics.ListCreateAPIView):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAdminUser]

class ProductListView(generics.ListAPIView):
    # Only show published products on public listing
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ['category', 'vendor', 'featured']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at', 'sales_count', 'featured']
    
    def get_queryset(self):
        # Order by: featured first, then newest first
        return Product.objects.filter(
            is_active=True, 
            status='published'
        ).select_related('vendor', 'category').order_by(
            '-featured',  # Featured products first
            '-created_at'  # Then newest products
        )

class ProductCreateView(generics.CreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, IsVendor]
    
    def perform_create(self, serializer):
        try:
            vendor_profile = self.request.user.vendor_profile
            product = serializer.save(vendor=vendor_profile, status='draft')
            
            # Handle image uploads
            images = self.request.FILES.getlist('images')
            for idx, image in enumerate(images):
                is_primary = self.request.data.get(f'image_{idx}_is_primary', 'false').lower() == 'true'
                order = int(self.request.data.get(f'image_{idx}_order', idx))
                ProductImage.objects.create(
                    product=product,
                    image=image,
                    is_primary=is_primary,
                    order=order
                )
            
            # Handle variations if provided
            import json
            variations_data = self.request.data.get('variations')
            if variations_data:
                try:
                    variations = json.loads(variations_data)
                    from .models import ProductVariation
                    for var in variations:
                        if var.get('name') and var.get('value'):
                            ProductVariation.objects.create(
                                product=product,
                                name=var['name'],
                                value=var['value'],
                                price_adjustment=var.get('price_adjustment', 0),
                                stock=var.get('stock', 0),
                                sku=var.get('sku', f"{product.sku}-{var['value']}")
                            )
                except:
                    pass
            
            # Update product status based on completeness
            product.update_status()
            
        except:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({
                'detail': 'Please complete your vendor profile setup before adding products.'
            })

class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated(), IsVendor()]
        return [permissions.AllowAny()]
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views += 1
        instance.save(update_fields=['views'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

class VendorProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, IsVendor]
    
    def get_queryset(self):
        try:
            return Product.objects.filter(vendor=self.request.user.vendor_profile)
        except:
            # User doesn't have a vendor profile yet
            return Product.objects.none()
