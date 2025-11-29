from django.contrib import admin
from .models import VendorProfile

@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'user', 'status', 'total_sales', 'total_orders', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['business_name', 'user__username', 'business_email']
    readonly_fields = ['total_sales', 'total_orders', 'rating', 'created_at', 'updated_at']
