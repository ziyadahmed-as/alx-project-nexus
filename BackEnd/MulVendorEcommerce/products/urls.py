from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

# Category endpoints
router.register(r'categories', views.CategoryViewSet, basename='category')

# Product endpoints (includes basic CRUD operations)
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

urlpatterns = [
    # Include all router URLs
    path('', include(router.urls)),
    
    # ======================
    # PRODUCT ENDPOINTS
    # ======================
    
    # Product CRUD operations (provided by ViewSet automatically):
    # POST   /products/          - Create new product
    # GET    /products/          - List all products
    # GET    /products/<pk>/     - Retrieve specific product
    # PUT    /products/<pk>/     - Update entire product
    # PATCH  /products/<pk>/     - Partial update product
    # DELETE /products/<pk>/     - Delete product
    
    # Product custom endpoints
    path('products/featured/', 
         views.ProductViewSet.as_view({'get': 'featured'}), 
         name='product-featured'),
    
    path('products/popular/', 
         views.ProductViewSet.as_view({'get': 'popular'}), 
         name='product-popular'),
    
    path('products/nearby/', 
         views.ProductViewSet.as_view({'get': 'nearby'}), 
         name='product-nearby'),
    
    path('products/above-rating/', 
         views.ProductViewSet.as_view({'get': 'above_rating'}), 
         name='product-above-rating'),
    
    path('products/<int:pk>/similar-nearby/', 
         views.ProductViewSet.as_view({'get': 'similar_nearby'}), 
         name='product-similar-nearby'),
    
    path('products/<int:pk>/toggle-activation/', 
         views.ProductViewSet.as_view({'post': 'toggle_activation'}), 
         name='product-toggle-activation'),
    
    path('products/my-products/', 
         views.ProductViewSet.as_view({'get': 'my_products'}), 
         name='product-my-products'),
    
    # ======================
    # PRODUCT IMAGE ENDPOINTS
    # ======================
    
    # ProductImage CRUD operations (provided by ViewSet automatically):
    # POST   /product-images/          - Create new product image
    # GET    /product-images/          - List all product images
    # GET    /product-images/<pk>/     - Retrieve specific product image
    # PUT    /product-images/<pk>/     - Update entire product image
    # PATCH  /product-images/<pk>/     - Partial update product image
    # DELETE /product-images/<pk>/     - Delete product image
    
    path('product-images/by-product/', 
         views.ProductImageViewSet.as_view({'get': 'product_images'}), 
         name='product-images-by-product'),
    
    # ======================
    # PRODUCT VARIANT ENDPOINTS
    # ======================
    
    # ProductVariant CRUD operations (provided by ViewSet automatically):
    # POST   /product-variants/          - Create new product variant
    # GET    /product-variants/          - List all product variants
    # GET    /product-variants/<pk>/     - Retrieve specific product variant
    # PUT    /product-variants/<pk>/     - Update entire product variant
    # PATCH  /product-variants/<pk>/     - Partial update product variant
    # DELETE /product-variants/<pk>/     - Delete product variant
    
    path('product-variants/by-product/', 
         views.ProductVariantViewSet.as_view({'get': 'product_variants'}), 
         name='product-variants-by-product'),
    
    # ======================
    # PRODUCT REVIEW ENDPOINTS
    # ======================
    
    # ProductReview CRUD operations (provided by ViewSet automatically):
    # POST   /product-reviews/          - Create new product review
    # GET    /product-reviews/          - List all product reviews
    # GET    /product-reviews/<pk>/     - Retrieve specific product review
    # PUT    /product-reviews/<pk>/     - Update entire product review
    # PATCH  /product-reviews/<pk>/     - Partial update product review
    # DELETE /product-reviews/<pk>/     - Delete product review
    
    path('product-reviews/<int:pk>/respond/', 
         views.ProductReviewViewSet.as_view({'post': 'respond'}), 
         name='review-respond'),
    
    path('product-reviews/<int:pk>/approve/', 
         views.ProductReviewViewSet.as_view({'post': 'approve'}), 
         name='review-approve'),
    
    # ======================
    # PRODUCT QUESTION ENDPOINTS
    # ======================
    
    # ProductQuestion CRUD operations (provided by ViewSet automatically):
    # POST   /product-questions/          - Create new product question
    # GET    /product-questions/          - List all product questions
    # GET    /product-questions/<pk>/     - Retrieve specific product question
    # PUT    /product-questions/<pk>/     - Update entire product question
    # PATCH  /product-questions/<pk>/     - Partial update product question
    # DELETE /product-questions/<pk>/     - Delete product question
    
    path('product-questions/<int:pk>/answer/', 
         views.ProductQuestionViewSet.as_view({'post': 'answer'}), 
         name='question-answer'),
    
    path('product-questions/<int:pk>/approve/', 
         views.ProductQuestionViewSet.as_view({'post': 'approve'}), 
         name='question-approve'),
    
    # ======================
    # VENDOR LOCATION ENDPOINTS
    # ======================
    
    path('vendor-locations/nearby/', 
         views.VendorLocationViewSet.as_view({'get': 'get_vendors_within_radius'}), 
         name='vendors-nearby'),
    
    path('vendor-locations/<int:pk>/coordinates/', 
         views.VendorLocationViewSet.as_view({'get': 'get_vendor_coordinates'}), 
         name='vendor-coordinates'),
    
    # ======================
    # CACHE MANAGEMENT
    # ======================
    
    path('cache-management/', 
         views.CacheManagementView.as_view(), 
         name='cache-management'),
]