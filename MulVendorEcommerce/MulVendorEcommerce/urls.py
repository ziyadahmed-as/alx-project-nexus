# In MulVendorEcommerce/urls.py (project level)
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('Users.urls')),
    path('api/', include('products.urls')),
    # path('api/', include('vendors.urls')),
    # path('api/', include('orders.urls')),  
]