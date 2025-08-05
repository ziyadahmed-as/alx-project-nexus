# In MulVendorEcommerce/urls.py (project level)
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('user/', include('Users.urls')),
    path('product/', include('products.urls')),
    path('order/', include('orders.urls')),
    
]