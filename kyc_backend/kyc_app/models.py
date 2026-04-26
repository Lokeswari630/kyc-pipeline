from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
import json


class User(AbstractUser):
    ROLE_CHOICES = [
        ('merchant', 'Merchant'),
        ('reviewer', 'Reviewer'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='merchant')

    def __str__(self):
        return f"{self.username} ({self.role})"


class KYCSubmission(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('more_info_requested', 'More Info Requested'),
    ]

    merchant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kyc_submissions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Personal Info
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)

    # Business Info
    business_name = models.CharField(max_length=255)
    business_type = models.CharField(max_length=100)
    monthly_volume = models.DecimalField(max_digits=15, decimal_places=2)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewer_notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"KYC-{self.id} ({self.merchant.username})"


class Document(models.Model):
    DOCUMENT_TYPES = [
        ('pan', 'PAN'),
        ('aadhaar', 'Aadhaar'),
        ('bank_statement', 'Bank Statement'),
    ]

    submission = models.ForeignKey(KYCSubmission, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    file = models.FileField(
        upload_to='kyc_documents/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('submission', 'document_type')

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.submission.id}"


class Notification(models.Model):
    EVENT_TYPES = [
        ('submission_created', 'Submission Created'),
        ('submitted_for_review', 'Submitted For Review'),
        ('review_started', 'Review Started'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('more_info_requested', 'More Info Requested'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    submission = models.ForeignKey(KYCSubmission, on_delete=models.CASCADE, related_name='notifications')
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.user.username}"
