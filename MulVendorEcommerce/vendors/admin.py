# # products/admin.py
# from django.contrib import admin
# from mptt.admin import MPTTModelAdmin
# from .models import Category, Product, ProductImage, ProductReview, ProductVariant, VendorProductRelation

# @admin.register(Category)
# class CategoryAdmin(MPTTModelAdmin):
#     list_display = ('name', 'parent', 'is_active', 'created_at')
#     list_filter = ('is_active',)
#     search_fields = ('name', 'description')
#     prepopulated_fields = {'slug': ('name',)}
#     mptt_level_indent = 20


# class ProductImageInline(admin.TabularInline):
#     model = ProductImage
#     extra = 1
#     fields = ('image', 'alt_text', 'is_main', 'order')
#     readonly_fields = ('created_at',)


# class ProductVariantInline(admin.TabularInline):
#     model = ProductVariant
#     extra = 1
#     fields = ('name', 'value', 'price_modifier', 'sku', 'stock', 'is_active')


# @admin.register(Product)
# class ProductAdmin(admin.ModelAdmin):
#     list_display = ('name', 'vendor', 'category', 'price', 'stock', 'status', 'is_active', 'created_at')
#     list_filter = ('status', 'is_active', 'category', 'vendor')
#     search_fields = ('name', 'description', 'sku', 'upc')
#     list_editable = ('status', 'is_active')
#     prepopulated_fields = {'slug': ('name',)}
#     readonly_fields = ('created_at', 'updated_at', 'published_at')
#     inlines = [ProductImageInline, ProductVariantInline]
#     fieldsets = (
#         (None, {
#             'fields': ('vendor', 'category', 'name', 'slug', 'description', 'specifications')
#         }),
#         ('Pricing & Inventory', {
#             'fields': ('price', 'discount_price', 'cost_price', 'stock', 'sku', 'upc')
#         }),
#         ('Status & Visibility', {
#             'fields': ('status', 'is_featured', 'is_active')
#         }),
#         ('Dates', {
#             'fields': ('created_at', 'updated_at', 'published_at'),
#             'classes': ('collapse',)
#         }),
#     )


# @admin.register(ProductReview)
# class ProductReviewAdmin(admin.ModelAdmin):
#     list_display = ('product', 'user', 'rating', 'title', 'is_approved', 'created_at')
#     list_filter = ('rating', 'is_approved')
#     search_fields = ('product__name', 'user__username', 'title')
#     list_editable = ('is_approved',)
#     readonly_fields = ('created_at', 'updated_at')


# @admin.register(VendorProductRelation)
# class VendorProductRelationAdmin(admin.ModelAdmin):
#     list_display = ('vendor', 'product', 'is_primary', 'commission_rate', 'created_at')
#     list_filter = ('is_primary', 'vendor')
#     search_fields = ('vendor__business_name', 'product__name')
#     list_editable = ('is_primary', 'commission_rate')
#     readonly_fields = ('created_at', 'updated_at')