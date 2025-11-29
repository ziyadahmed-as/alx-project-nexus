from django.contrib import admin
from .models import Category, Product, ProductImage, ProductVariation

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'is_active']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'vendor', 'price', 'stock', 'is_active', 'sales_count']
    list_filter = ['is_active', 'featured', 'category']
    search_fields = ['name', 'sku']
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(ProductImage)
admin.site.register(ProductVariation)
