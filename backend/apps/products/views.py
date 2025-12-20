from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.core.cache import cache
from .models import Category, Product, ProductImage
from .serializers import CategorySerializer, ProductSerializer, ProductImageSerializer
from apps.vendors.permissions import IsVendor
from .recommendations import ProductRecommendations

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
    search_fields = ['name', 'description', 'vendor__business_name', 'vendor__vendor_name']
    ordering_fields = ['price', 'created_at', 'sales_count', 'featured']
    
    def get_queryset(self):
        queryset = Product.objects.filter(
            is_active=True, 
            status='published',
            vendor__is_active=True,  # Exclude products from suspended vendors
            vendor__status='approved'  # Only show products from approved vendors
        ).select_related('vendor', 'category').order_by(
            '-featured',  # Featured products first
            '-created_at'  # Then newest products
        )
        
        # Filter by vendor name or business name if provided
        vendor_search = self.request.query_params.get('vendor_name', None)
        if vendor_search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(vendor__vendor_name__icontains=vendor_search) |
                Q(vendor__business_name__icontains=vendor_search)
            )
        
        # Filter by location (city, state, or country)
        location = self.request.query_params.get('location', None)
        if location:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(vendor__office_city__icontains=location) |
                Q(vendor__office_state__icontains=location) |
                Q(vendor__office_country__icontains=location)
            )
        
        # Filter by city specifically
        city = self.request.query_params.get('city', None)
        if city:
            queryset = queryset.filter(vendor__office_city__icontains=city)
        
        # Filter by state/region
        state = self.request.query_params.get('state', None)
        if state:
            queryset = queryset.filter(vendor__office_state__icontains=state)
        
        # Filter by country
        country = self.request.query_params.get('country', None)
        if country:
            queryset = queryset.filter(vendor__office_country__icontains=country)
        
        # Filter by geographic coordinates (radius search)
        lat = self.request.query_params.get('lat', None)
        lng = self.request.query_params.get('lng', None)
        radius = self.request.query_params.get('radius', 50)  # Default 50km radius
        
        if lat and lng:
            try:
                from django.db.models import F
                from decimal import Decimal
                import math
                
                lat = Decimal(lat)
                lng = Decimal(lng)
                radius = float(radius)
                
                # Simple bounding box filter (approximate)
                # 1 degree latitude ≈ 111km
                # 1 degree longitude ≈ 111km * cos(latitude)
                lat_range = Decimal(radius / 111.0)
                lng_range = Decimal(radius / (111.0 * math.cos(math.radians(float(lat)))))
                
                queryset = queryset.filter(
                    vendor__latitude__isnull=False,
                    vendor__longitude__isnull=False,
                    vendor__latitude__gte=lat - lat_range,
                    vendor__latitude__lte=lat + lat_range,
                    vendor__longitude__gte=lng - lng_range,
                    vendor__longitude__lte=lng + lng_range
                )
            except (ValueError, TypeError):
                pass
        
        return queryset

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
            
            # Update product status based on completeness
            product.update_status()
            
        except AttributeError:
             from rest_framework.exceptions import ValidationError
             raise ValidationError({
                'detail': 'Vendor profile not found.'
            })
        except Exception as e:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({
                'detail': str(e)
            })

    def create(self, request, *args, **kwargs):
        # Check if vendor is approved
        try:
             vendor_profile = request.user.vendor_profile
             if vendor_profile.status != 'approved' or not vendor_profile.is_active:
                 return Response(
                     {'detail': 'Your vendor account must be approved by an admin before you can add products.'},
                     status=status.HTTP_403_FORBIDDEN
                 )
        except:
             return Response(
                 {'detail': 'You must have a vendor profile to add products.'},
                 status=status.HTTP_403_FORBIDDEN
             )
        return super().create(request, *args, **kwargs)

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
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        # Verify the product belongs to the requesting vendor
        if hasattr(request.user, 'vendor_profile'):
            if instance.vendor != request.user.vendor_profile:
                return Response(
                    {'error': 'You do not have permission to edit this product'},
                    status=status.HTTP_403_FORBIDDEN
                )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Verify the product belongs to the requesting vendor
        if hasattr(request.user, 'vendor_profile'):
            if instance.vendor != request.user.vendor_profile:
                return Response(
                    {'error': 'You do not have permission to delete this product'},
                    status=status.HTTP_403_FORBIDDEN
                )
        return super().destroy(request, *args, **kwargs)

class VendorProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, IsVendor]
    filterset_fields = ['status', 'is_active', 'featured']
    search_fields = ['name', 'description', 'sku']
    ordering_fields = ['created_at', 'price', 'sales_count']
    
    def get_queryset(self):
        try:
            vendor_profile = self.request.user.vendor_profile
            queryset = Product.objects.filter(vendor=vendor_profile)
            
            # If vendor is suspended, they can still see their products but with a note
            if not vendor_profile.is_active:
                # Add a message in the response (handled in serializer or view)
                pass
            
            return queryset
        except:
            # User doesn't have a vendor profile yet
            return Product.objects.none()

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def product_recommendations(request, pk):
    """Get recommendations for a specific product"""
    try:
        product = Product.objects.get(pk=pk, is_active=True, status='published')
        recommendations = ProductRecommendations.get_you_may_also_like(
            product, 
            user=request.user if request.user.is_authenticated else None,
            limit=8
        )
        serializer = ProductSerializer(recommendations, many=True)
        return Response(serializer.data)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def similar_products(request, pk):
    """Get similar products"""
    try:
        product = Product.objects.get(pk=pk, is_active=True, status='published')
        similar = ProductRecommendations.get_similar_products(product, limit=8)
        serializer = ProductSerializer(similar, many=True)
        return Response(serializer.data)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def trending_products(request):
    """Get trending products"""
    trending = ProductRecommendations.get_trending_products(limit=12)
    serializer = ProductSerializer(trending, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def best_sellers(request):
    """Get best selling products"""
    best_sellers = ProductRecommendations.get_best_sellers(limit=12)
    serializer = ProductSerializer(best_sellers, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def personalized_recommendations(request):
    """Get personalized recommendations for the user"""
    recommendations = ProductRecommendations.get_personalized_recommendations(
        user=request.user if request.user.is_authenticated else None,
        limit=12
    )
    serializer = ProductSerializer(recommendations, many=True)
    return Response(serializer.data)

class AdminProductListView(generics.ListAPIView):
    """Admin view to see all products including from suspended vendors"""
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    filterset_fields = ['category', 'vendor', 'featured', 'status', 'is_active']
    search_fields = ['name', 'description', 'sku', 'vendor__business_name', 'vendor__vendor_name']
    ordering_fields = ['price', 'created_at', 'sales_count', 'featured']
    
    def get_queryset(self):
        queryset = Product.objects.all().select_related('vendor', 'category')
        
        # Filter by vendor status if provided
        vendor_status = self.request.query_params.get('vendor_status', None)
        if vendor_status:
            if vendor_status == 'suspended':
                queryset = queryset.filter(vendor__is_active=False)
            elif vendor_status == 'active':
                queryset = queryset.filter(vendor__is_active=True)
        
        # Filter by vendor name or business name
        vendor_search = self.request.query_params.get('vendor_name', None)
        if vendor_search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(vendor__vendor_name__icontains=vendor_search) |
                Q(vendor__business_name__icontains=vendor_search)
            )
        
        return queryset.order_by('-created_at')

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def track_product_share(request, pk):
    """Track when a product is shared on social media"""
    try:
        product = Product.objects.get(pk=pk)
        platform = request.data.get('platform', 'unknown')
        
        # You can add a shares field to track this or log it
        # For now, we'll just return success
        # In future, you could add: product.shares += 1; product.save()
        
        return Response({
            'message': f'Product shared on {platform}',
            'product_id': product.id,
            'product_name': product.name
        })
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def vendor_locations(request):
    """Get all vendor locations for map display"""
    from apps.vendors.models import VendorProfile
    from django.db.models import Count, Q
    
    vendors = VendorProfile.objects.filter(
        is_active=True,
        status='approved',
        latitude__isnull=False,
        longitude__isnull=False
    ).annotate(
        product_count=Count('products', filter=Q(products__is_active=True, products__status='published'))
    ).values(
    ).values(
        'id', 'business_name', 'city', 'state', 
        'country', 'latitude', 'longitude', 'product_count'
    )
    
    return Response(list(vendors))

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsVendor])
def generate_tiktok_dashboard_link(request, pk):
    """Generate a special TikTok dashboard link for vendors to share their products"""
    try:
        product = Product.objects.get(pk=pk)
        
        # Verify the product belongs to the requesting vendor
        if product.vendor.user != request.user:
            return Response(
                {'error': 'You do not have permission to generate a link for this product'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Generate the dashboard link with tracking parameters
        from django.conf import settings
        base_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        
        # Create a special dashboard link with UTM parameters for TikTok
        dashboard_link = (
            f"{base_url}/products/{product.id}"
            f"?utm_source=tiktok"
            f"&utm_medium=social"
            f"&utm_campaign=vendor_share"
            f"&vendor_id={product.vendor.id}"
        )
        
        # Also generate a vendor dashboard preview link
        vendor_dashboard_link = f"{base_url}/vendor/products/{product.id}/share"
        
        return Response({
            'product_id': product.id,
            'product_name': product.name,
            'product_url': f"{base_url}/products/{product.id}",
            'tiktok_dashboard_link': dashboard_link,
            'vendor_dashboard_link': vendor_dashboard_link,
            'share_text': f"Check out {product.name} - Only ${product.price}! {product.description[:100]}...",
            'hashtags': ['ecommerce', 'shopping', 'deals', product.category.name.lower() if product.category else 'products'],
        })
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
