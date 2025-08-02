from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet,
    ProductViewSet,
    ProductImageViewSet,
    ProductReviewViewSet,
    ProductQuestionViewSet
)

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'product-images', ProductImageViewSet, basename='product-image')
router.register(r'reviews', ProductReviewViewSet, basename='review')
router.register(r'questions', ProductQuestionViewSet, basename='question')

# Schema view for Swagger documentation
schema_view = get_schema_view(
   openapi.Info(
      title="E-Commerce API",
      default_version='v1',
      description="""
      API documentation for Multi-Vendor E-Commerce Platform.
      
      Features include:
      - Product management with Redis caching
      - Location-based product recommendations
      - Vendor and employee permissions
      - Product reviews and Q&A system
      """,
      terms_of_service="https://www.example.com/terms/",
      contact=openapi.Contact(email="api@example.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # API endpoints
    path('', include(router.urls)),
    
    # Swagger documentation URLs
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Additional custom endpoints
    path('products/<int:pk>/similar-nearby/', 
         ProductViewSet.as_view({'get': 'similar_nearby'}), 
         name='product-similar-nearby'),
    path('products/nearby/', 
         ProductViewSet.as_view({'get': 'nearby'}), 
         name='product-nearby'),
    path('products/featured/', 
         ProductViewSet.as_view({'get': 'featured'}), 
         name='product-featured'),
    path('products/popular/', 
         ProductViewSet.as_view({'get': 'popular'}), 
         name='product-popular'),
    path('products/my-products/', 
         ProductViewSet.as_view({'get': 'my_products'}), 
         name='product-my-products'),
    path('categories/<slug:slug>/products/', 
         CategoryViewSet.as_view({'get': 'products'}), 
         name='category-products'),
    path('product-images/product-images/', 
         ProductImageViewSet.as_view({'get': 'product_images'}), 
         name='product-images-list'),
    path('reviews/<int:pk>/respond/', 
         ProductReviewViewSet.as_view({'post': 'respond'}), 
         name='review-respond'),
    path('questions/<int:pk>/answer/', 
         ProductQuestionViewSet.as_view({'post': 'answer'}), 
         name='question-answer'),
]