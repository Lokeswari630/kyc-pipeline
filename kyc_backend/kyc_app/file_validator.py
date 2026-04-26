"""
File upload validation for KYC documents.
"""

import os
from django.core.exceptions import ValidationError


ALLOWED_EXTENSIONS = ['pdf', 'jpg', 'jpeg', 'png']
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


class FileValidationError(Exception):
    """Exception for file validation errors."""
    pass


def validate_kyc_document(file_obj):
    """
    Validate KYC document file.
    
    Args:
        file_obj: Django UploadedFile object
        
    Raises:
        FileValidationError: If validation fails
        
    Returns:
        bool: True if file is valid
    """
    if not file_obj:
        raise FileValidationError("No file provided")
    
    # Check file size
    if file_obj.size > MAX_FILE_SIZE:
        size_mb = file_obj.size / (1024 * 1024)
        raise FileValidationError(
            f"File size ({size_mb:.2f} MB) exceeds maximum allowed size (5 MB)"
        )
    
    # Check file extension
    ext = os.path.splitext(file_obj.name)[1].lower().lstrip('.')
    if ext not in ALLOWED_EXTENSIONS:
        raise FileValidationError(
            f"File type '.{ext}' not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Basic MIME type check
    if file_obj.content_type not in [
        'application/pdf',
        'image/jpeg',
        'image/jpg',
        'image/png',
    ]:
        raise FileValidationError(
            f"Invalid file MIME type: {file_obj.content_type}"
        )
    
    return True


def get_file_size_mb(file_obj):
    """Get file size in MB."""
    return file_obj.size / (1024 * 1024)
