from rest_framework.permissions import BasePermission

class IsSuperAdmin(BasePermission):
    """
    Permission for superuser access.
    Grants access only to authenticated users with superuser status.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)


class IsVendorOwner(BasePermission):
    """
    Object-level permission to allow access only to the owner of the vendor-related object.
    Assumes the object has a 'vendor' attribute, and the user has a 'vendor' profile.
    """
    def has_object_permission(self, request, view, obj):
        return bool(
            request.user 
            and request.user.is_authenticated 
            and hasattr(request.user, 'vendor') 
            and getattr(obj, 'vendor', None) == request.user.vendor
        )


class IsProfileOwner(BasePermission):
    """
    Object-level permission to allow access only to the owner of the profile.
    - If the object is a User instance, it must match the request.user.
    - If the object has a 'user' attribute, it must match the request.user.
    """
    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False
        
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return obj == request.user
    
# -------------------------------       
# IsVendorEmployee(BasePermission):

#-- Object-level permission to allow access only to vendor employees.
class IsVendorEmployee(BasePermission):
    """
    Permission for vendor employees.
    Grants access only to authenticated users who are employees of the vendor.
    """ 
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False    
        if hasattr(request.user, 'vendor_employee'):
            return request.user.vendor_employee.is_active
        return False
# -------------------------------