from django.urls import path
from .views import (
    CategoryListView, CategoryDetailView, ProductListView, ProductCreateView,
    ProductDetailView, VendorProductListView, AdminProductListView,
    product_recommendations, similar_products, trending_products, 
    best_sellers, personalized_recommendations, track_product_share,
    generate_tiktok_dashboard_link, vendor_locations
)

urlpatterns = [
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),
    path('', ProductListView.as_view(), name='product-list'),
    path('admin/all/', AdminProductListView.as_view(), name='admin-product-list'),
    path('create/', ProductCreateView.as_view(), name='product-create'),
    path('my-products/', VendorProductListView.as_view(), name='vendor-products'),
    path('vendor-locations/', vendor_locations, name='vendor-locations'),
    path('recommendations/trending/', trending_products, name='trending-products'),
    path('recommendations/best-sellers/', best_sellers, name='best-sellers'),
    path('recommendations/personalized/', personalized_recommendations, name='personalized-recommendations'),
    path('<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('<int:pk>/recommendations/', product_recommendations, name='product-recommendations'),
    path('<int:pk>/similar/', similar_products, name='similar-products'),
    path('<int:pk>/share/', track_product_share, name='track-product-share'),
    path('<int:pk>/tiktok-link/', generate_tiktok_dashboard_link, name='generate-tiktok-link'),
]
