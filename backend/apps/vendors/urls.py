from django.urls import path
from .views import (
    VendorProfileCreateView, VendorProfileDetailView, VendorPublicDetailView,
    VendorListView, VendorManagementView, verify_vendor
)

urlpatterns = [
    path('', VendorListView.as_view(), name='vendor-list'),
    path('create/', VendorProfileCreateView.as_view(), name='vendor-create'),
    path('profile/', VendorProfileDetailView.as_view(), name='vendor-profile'),
    path('manage/', VendorManagementView.as_view(), name='vendor-manage'),
    path('<int:pk>/', VendorPublicDetailView.as_view(), name='vendor-public-detail'),
    path('<int:pk>/verify/', verify_vendor, name='vendor-verify'),
]
