from rest_framework import permissions

class IsSuperAdmin(permissions.BasePermission):
    """
    Allows access only to users with superuser status.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)

class IsVendorOwner(permissions.BasePermission):
    """
    Allows access only to the vendor owner of the object.
    Assumes 'obj' has a 'user' attribute linking to the owner user.
    """
    def has_object_permission(self, request, view, obj):
        return bool(request.user and request.user.is_authenticated and obj.user == request.user)

class IsProfileOwner(permissions.BasePermission):
    """
    Allows access if the object is the user themselves or
    the user associated with the profile (obj.user).
    Useful for user profiles or related objects.
    """
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_authenticated:
            # If obj is a User instance
            if hasattr(obj, 'username'):  
                return obj == request.user
            # If obj has a 'user' attribute (e.g., Profile)
            if hasattr(obj, 'user'):
                return obj.user == request.user
        return False
