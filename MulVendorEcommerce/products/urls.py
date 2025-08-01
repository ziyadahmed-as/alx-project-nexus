# urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet,
    ProductViewSet,
    ProductImageViewSet,
    ProductReviewViewSet,
    ProductQuestionViewSet,
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'product-images', ProductImageViewSet, basename='productimage')
router.register(r'product-reviews', ProductReviewViewSet, basename='productreview')
router.register(r'product-questions', ProductQuestionViewSet, basename='productquestion')

urlpatterns = [
    path('', include(router.urls)),
]
