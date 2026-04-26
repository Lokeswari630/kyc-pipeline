"""
Django admin configuration for KYC app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, KYCSubmission, Document, Notification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'role', 'is_staff']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role', {'fields': ('role',)}),
    )


@admin.register(KYCSubmission)
class KYCSubmissionAdmin(admin.ModelAdmin):
    list_display = ['id', 'merchant', 'status', 'business_name', 'submitted_at']
    list_filter = ['status', 'created_at']
    search_fields = ['merchant__username', 'business_name', 'email']
    readonly_fields = ['created_at', 'updated_at', 'submitted_at', 'reviewed_at']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['id', 'submission', 'document_type', 'uploaded_at']
    list_filter = ['document_type', 'uploaded_at']
    readonly_fields = ['uploaded_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'event_type', 'created_at', 'is_read']
    list_filter = ['event_type', 'is_read', 'created_at']
    readonly_fields = ['created_at', 'payload']
