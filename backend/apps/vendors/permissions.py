from rest_framework import permissions

class IsVendorOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or request.user.role == 'admin'

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'admin'

class IsVendor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'vendor'
