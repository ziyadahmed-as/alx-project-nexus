from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

# Category endpoints
router.register(r'categories', views.CategoryViewSet, basename='category')

# Product endpoints
router.register(r'products', views.ProductViewSet, basename='product')

# Product Image endpoints
router.register(r'product-images', views.ProductImageViewSet, basename='product-image')

# Product Variant endpoints
router.register(r'product-variants', views.ProductVariantViewSet, basename='product-variant')

# Product Review endpoints
router.register(r'product-reviews', views.ProductReviewViewSet, basename='product-review')

# Product Question endpoints
router.register(r'product-questions', views.ProductQuestionViewSet, basename='product-question')

# Vendor Location endpoints
router.register(r'vendor-locations', views.VendorLocationViewSet, basename='vendor-location')

# Additional URL patterns that don't fit the ViewSet pattern
urlpatterns = [
    path('', include(router.urls)),
    
    # Cache management endpoint
    path('cache-management/', views.CacheManagementView.as_view(), name='cache-management'),
    
    # Product custom endpoints
    path('products/featured/', views.ProductViewSet.as_view({'get': 'featured'}), name='product-featured'),
    path('products/popular/', views.ProductViewSet.as_view({'get': 'popular'}), name='product-popular'),
    path('products/nearby/', views.ProductViewSet.as_view({'get': 'nearby'}), name='product-nearby'),
    
    # Product Image custom endpoints
    path('product-images/by-product/', views.ProductImageViewSet.as_view({'get': 'product_images'}), name='product-images-by-product'),
    
    # Product Variant custom endpoints
    path('product-variants/by-product/', views.ProductVariantViewSet.as_view({'get': 'product_variants'}), name='product-variants-by-product'),
    
    # Product Review custom endpoints
    path('product-reviews/<int:pk>/respond/', views.ProductReviewViewSet.as_view({'post': 'respond'}), name='review-respond'),
    path('product-reviews/<int:pk>/approve/', views.ProductReviewViewSet.as_view({'post': 'approve'}), name='review-approve'),
    
    # Product Question custom endpoints
    path('product-questions/<int:pk>/answer/', views.ProductQuestionViewSet.as_view({'post': 'answer'}), name='question-answer'),
    path('product-questions/<int:pk>/approve/', views.ProductQuestionViewSet.as_view({'post': 'approve'}), name='question-approve'),
    
    # Vendor Location custom endpoints
    path('vendor-locations/nearby/', views.VendorLocationViewSet.as_view({'get': 'get_vendors_within_radius'}), name='vendors-nearby'),
    path('vendor-locations/<int:pk>/coordinates/', views.VendorLocationViewSet.as_view({'get': 'get_vendor_coordinates'}), name='vendor-coordinates'),
]