"""
Permission classes for DRF.
"""

from rest_framework import permissions


class IsMerchant(permissions.BasePermission):
    """Only merchants can access this endpoint."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'merchant'


class IsReviewer(permissions.BasePermission):
    """Only reviewers can access this endpoint."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'reviewer'


class IsMerchantOrReadOnlyReviewer(permissions.BasePermission):
    """
    Merchants can create/edit their own submissions.
    Reviewers can only view (read-only).
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Reviewers can view but not modify
        if request.user.role == 'reviewer':
            return request.method in permissions.SAFE_METHODS
        
        # Merchants can only access their own submissions
        if request.user.role == 'merchant':
            return obj.merchant == request.user
        
        return False


class IsOwnerOrReviewer(permissions.BasePermission):
    """
    Merchants can access their own submissions.
    Reviewers can access all submissions.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'reviewer':
            return True
        if request.user.role == 'merchant':
            return obj.merchant == request.user
        return False
