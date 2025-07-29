from rest_framework import permissions

# User permissions for the application
class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user.is_authenticated and 
                request.user.role == 'ADMIN' and 
                hasattr(request.user, 'admin_profile') and
                request.user.admin_profile.access_level == 'SUPER')
       
# This permission allows access to admin users with super admin privileges.
class IsVendorOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

# This permission allows access to admin users with admin privileges.
class IsProfileOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj == request.user or obj.user == request.user


