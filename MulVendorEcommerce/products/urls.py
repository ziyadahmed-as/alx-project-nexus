from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet,
    ProductViewSet,
    ProductImageViewSet,
    ProductReviewViewSet,
    ProductQuestionViewSet
)

router = DefaultRouter()

# Category URLs
router.register(r'categories', CategoryViewSet, basename='category')

# Product URLs
router.register(r'products', ProductViewSet, basename='product')

# Product Image URLs
router.register(r'product-images', ProductImageViewSet, basename='productimage')

# Product Review URLs
router.register(r'reviews', ProductReviewViewSet, basename='review')

# Product Question URLs
router.register(r'questions', ProductQuestionViewSet, basename='question')

# Additional custom URL patterns for product actions
product_urls = [
    path('products/<int:pk>/toggle-activation/', 
         ProductViewSet.as_view({'post': 'toggle_activation'}), 
         name='product-toggle-activation'),
    path('products/my-products/', 
         ProductViewSet.as_view({'get': 'my_products'}), 
         name='product-my-products'),
    path('products/nearby/', 
         ProductViewSet.as_view({'get': 'nearby'}), 
         name='product-nearby'),
    path('products/<int:pk>/similar-nearby/', 
         ProductViewSet.as_view({'get': 'similar_nearby'}), 
         name='product-similar-nearby'),
]

# Review custom URLs
review_urls = [
    path('reviews/<int:pk>/respond/', 
         ProductReviewViewSet.as_view({'post': 'respond'}), 
         name='review-respond'),
]

# Question custom URLs
question_urls = [
    path('questions/<int:pk>/answer/', 
         ProductQuestionViewSet.as_view({'post': 'answer'}), 
         name='question-answer'),
]

urlpatterns = [
    path('', include(router.urls)),
    path('', include(product_urls)),
    path('', include(review_urls)),
    path('', include(question_urls)),
]
