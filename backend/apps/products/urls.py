from django.urls import path
from .views import (
    CategoryListView, CategoryDetailView, ProductListView, ProductCreateView,
    ProductDetailView, VendorProductListView, product_recommendations,
    similar_products, trending_products, best_sellers, personalized_recommendations
)

urlpatterns = [
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),
    path('', ProductListView.as_view(), name='product-list'),
    path('create/', ProductCreateView.as_view(), name='product-create'),
    path('my-products/', VendorProductListView.as_view(), name='vendor-products'),
    path('recommendations/trending/', trending_products, name='trending-products'),
    path('recommendations/best-sellers/', best_sellers, name='best-sellers'),
    path('recommendations/personalized/', personalized_recommendations, name='personalized-recommendations'),
    path('<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('<int:pk>/recommendations/', product_recommendations, name='product-recommendations'),
    path('<int:pk>/similar/', similar_products, name='similar-products'),
]
