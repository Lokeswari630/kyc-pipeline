"""
DRF Serializers for KYC app.
"""

from rest_framework import serializers
from .models import User, KYCSubmission, Document, Notification
from .file_validator import validate_kyc_document, FileValidationError


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role']
        read_only_fields = ['id']


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'document_type', 'file', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']

    def validate_file(self, value):
        try:
            validate_kyc_document(value)
        except FileValidationError as e:
            raise serializers.ValidationError(str(e))
        return value


class KYCSubmissionSerializer(serializers.ModelSerializer):
    documents = DocumentSerializer(many=True, read_only=True)
    merchant_username = serializers.CharField(source='merchant.username', read_only=True)
    allowed_transitions = serializers.SerializerMethodField()

    class Meta:
        model = KYCSubmission
        fields = [
            'id', 'merchant_username', 'status',
            'name', 'email', 'phone',
            'business_name', 'business_type', 'monthly_volume',
            'documents', 'created_at', 'updated_at',
            'submitted_at', 'reviewed_at', 'reviewer_notes',
            'allowed_transitions'
        ]
        read_only_fields = [
            'id', 'merchant_username', 'status', 'created_at', 'updated_at',
            'submitted_at', 'reviewed_at', 'allowed_transitions'
        ]

    def get_allowed_transitions(self, obj):
        """Return allowed state transitions for this submission."""
        from .state_machine import get_allowed_transitions
        return get_allowed_transitions(obj.status)


class NotificationSerializer(serializers.ModelSerializer):
    submission_id = serializers.IntegerField(source='submission.id', read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'submission_id', 'event_type', 'payload', 'created_at', 'is_read']
        read_only_fields = ['id', 'event_type', 'payload', 'created_at']


class KYCDetailSerializer(KYCSubmissionSerializer):
    """Extended serializer with all details including notifications."""
    notifications = NotificationSerializer(many=True, read_only=True)

    class Meta(KYCSubmissionSerializer.Meta):
        fields = KYCSubmissionSerializer.Meta.fields + ['notifications']


class ChangeStatusSerializer(serializers.Serializer):
    """Serializer for changing submission status."""
    new_status = serializers.ChoiceField(choices=[
        'draft', 'submitted', 'under_review', 'approved', 'rejected', 'more_info_requested'
    ])
    reviewer_notes = serializers.CharField(required=False, allow_blank=True)

    def validate_new_status(self, value):
        if value not in ['draft', 'submitted', 'under_review', 'approved', 'rejected', 'more_info_requested']:
            raise serializers.ValidationError(f"Invalid status: {value}")
        return value


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
