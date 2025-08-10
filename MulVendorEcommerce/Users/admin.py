# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin
# import uuid
# from .models import (
#     User, CustomerProfile, Vendor, 
#     AdminProfile, VendorEmployee, Address
# )

# # Custom User Admin
# class CustomUserAdmin(UserAdmin):
#     model = User
#     list_display = (
#         'email', 'first_name', 'last_name', 
#         'role', 'is_verified', 'is_active',
#         'last_active', 'created_at'
#     )
#     list_filter = (
#         'role', 'is_verified', 'is_active', 
#         'is_staff', 'is_superuser', 'created_at'
#     )
#     search_fields = ('email', 'first_name', 'last_name', 'phone_number')
#     ordering = ('-created_at',)
#     readonly_fields = ('last_active', 'created_at', 'updated_at')
    
#     fieldsets = (
#         (None, {'fields': ('email', 'password')}),
#         ('Personal Info', {'fields': (
#             'first_name', 'last_name', 'phone_number'
#         )}),
#         ('Permissions', {'fields': (
#             'is_active', 'is_verified', 'is_staff', 
#             'is_superuser', 'role', 'groups', 
#             'user_permissions'
#         )}),
#         ('Important Dates', {'fields': (
#             'last_login', 'last_active', 
#             'created_at', 'updated_at'
#         )}),
#     )
    
#     add_fieldsets = (
#         (None, {
#             'classes': ('wide',),
#             'fields': (
#                 'email', 'first_name', 'last_name',
#                 'password1', 'password2', 'is_staff', 
#                 'is_active', 'role'
#             ),
#         }),
#     )

# @admin.register(CustomerProfile)
# class CustomerProfileAdmin(admin.ModelAdmin):
#     list_display = (
#         'user', 'age', 'newsletter_subscription',
#         'preferred_language', 'created_at'
#     )
#     list_filter = (
#         'newsletter_subscription', 'preferred_language',
#         'created_at'
#     )
#     search_fields = (
#         'user__email', 'user__first_name', 
#         'user__last_name'
#     )
#     readonly_fields = ('age', 'created_at', 'updated_at')
#     raw_id_fields = ('user',)

# @admin.register(Vendor)
# class VendorAdmin(admin.ModelAdmin):
#     list_display = ('user', 'company_name_display', 'business_type', 'verification_status')
#     list_select_related = ('user',)
    
#     def company_name_display(self, obj):
#         return obj.company_name or "N/A"
#     company_name_display.short_description = 'Company Name'
#     company_name_display.admin_order_field = 'company_name'

# @admin.register(AdminProfile)
# class AdminProfileAdmin(admin.ModelAdmin):
#     list_display = (
#         'user', 'department', 'position',
#         'access_level', 'created_at'
#     )
#     list_filter = ('department', 'access_level', 'created_at')
#     search_fields = (
#         'user__email', 'position', 
#         'department'
#     )
#     readonly_fields = ('created_at', 'updated_at')
#     raw_id_fields = ('user',)

# @admin.register(VendorEmployee)
# class VendorEmployeeAdmin(admin.ModelAdmin):
#     list_display = (
#         'user', 'vendor', 'role', 
#         'department', 'is_active', 'hire_date'
#     )
#     list_filter = (
#         'vendor', 'role', 'department',
#         'is_active', 'hire_date'
#     )
#     search_fields = (
#         'user__email', 'employee_id',
#         'vendor__company_name'
#     )
#     readonly_fields = ('created_at', 'updated_at')
#     raw_id_fields = ('user', 'vendor')
#     list_select_related = ('user', 'vendor')

# @admin.register(Address)
# class AddressAdmin(admin.ModelAdmin):
#     list_display = (
#         'user', 'recipient_name', 'address_type',
#         'city', 'state', 'country', 'is_default'
#     )
#     list_filter = (
#         'address_type', 'country', 'is_default',
#         'created_at'
#     )
#     search_fields = (
#         'user__email', 'recipient_name',
#         'street_address', 'city', 'postal_code'
#     )
#     readonly_fields = (
#         'created_at', 'updated_at', 
#         'get_google_maps_url'
#     )
#     raw_id_fields = ('user',)
#     list_select_related = ('user',)

# # Register User model separately to ensure proper ordering
# admin.site.register(User, CustomUserAdmin)