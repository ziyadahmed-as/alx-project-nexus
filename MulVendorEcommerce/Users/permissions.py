from rest_framework import permissions

# User permissions for the application
class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser      
# This permission allows access to admin users with super admin privileges.
class IsVendorOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

# This permission allows access to admin users with admin privileges.
class IsProfileOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj == request.user or obj.user == request.user


