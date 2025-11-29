from django.urls import path
from .views import (
    CategoryListView, CategoryDetailView, ProductListView, ProductCreateView,
    ProductDetailView, VendorProductListView
)

urlpatterns = [
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),
    path('', ProductListView.as_view(), name='product-list'),
    path('create/', ProductCreateView.as_view(), name='product-create'),
    path('<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('my-products/', VendorProductListView.as_view(), name='vendor-products'),
]
