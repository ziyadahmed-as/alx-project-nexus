from django.urls import path, include
from . import views

urlpatterns = [
    # Categories
    path('categories/', views.CategoryViewSet.as_view({'get': 'list', 'post': 'create'}), name='category-list'),
    path('categories/<slug:slug>/', views.CategoryViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='category-detail'),
    path('categories/<slug:slug>/products/', views.CategoryViewSet.as_view({'get': 'products'}), name='category-products'),
    
    # Products
    path('products/', views.ProductViewSet.as_view({'get': 'list', 'post': 'create'}), name='product-list'),
    path('products/<int:pk>/', views.ProductViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='product-detail'),
    path('products/<int:pk>/toggle-activation/', views.ProductViewSet.as_view({'post': 'toggle_activation'}), name='product-toggle-activation'),
    path('products/<int:pk>/similar-nearby/', views.ProductViewSet.as_view({'get': 'similar_nearby'}), name='product-similar-nearby'),
    path('products/my-products/', views.ProductViewSet.as_view({'get': 'my_products'}), name='product-my-products'),
    path('products/featured/', views.ProductViewSet.as_view({'get': 'featured'}), name='product-featured'),
    path('products/popular/', views.ProductViewSet.as_view({'get': 'popular'}), name='product-popular'),
    path('products/nearby/', views.ProductViewSet.as_view({'get': 'nearby'}), name='product-nearby'),
    
    # Product Images
    path('product-images/', views.ProductImageViewSet.as_view({'get': 'list', 'post': 'create'}), name='product-image-list'),
    path('product-images/<int:pk>/', views.ProductImageViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='product-image-detail'),
    path('product-images/product-images/', views.ProductImageViewSet.as_view({'get': 'product_images'}), name='product-images-for-product'),
    
    # Reviews
    path('reviews/', views.ProductReviewViewSet.as_view({'get': 'list', 'post': 'create'}), name='review-list'),
    path('reviews/<int:pk>/', views.ProductReviewViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='review-detail'),
    path('reviews/<int:pk>/respond/', views.ProductReviewViewSet.as_view({'post': 'respond'}), name='review-respond'),
    
    # Questions
    path('questions/', views.ProductQuestionViewSet.as_view({'get': 'list', 'post': 'create'}), name='question-list'),
    path('questions/<int:pk>/', views.ProductQuestionViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='question-detail'),
    path('questions/<int:pk>/answer/', views.ProductQuestionViewSet.as_view({'post': 'answer'}), name='question-answer'),
    
    # Vendor Locations
    path('vendor-locations/get-vendors-within-radius/', views.VendorLocationViewSet.as_view({'get': 'get_vendors_within_radius'}), name='vendor-locations-within-radius'),
    path('vendor-locations/<int:pk>/get-vendor-coordinates/', views.VendorLocationViewSet.as_view({'get': 'get_vendor_coordinates'}), name='vendor-coordinates'),
    
    # Cache Management
    path('cache-management/', views.CacheManagementView.as_view(), name='cache-management'),
    
    # API Auth
    path('api-auth/', include('rest_framework.urls')),
]