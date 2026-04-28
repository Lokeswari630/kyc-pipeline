"""
DRF Views for KYC app API.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.authtoken.models import Token
from django.utils import timezone
from django.contrib.auth import authenticate
from django.db.models import Q, Count, F
from datetime import timedelta

from .models import User, KYCSubmission, Document, Notification
from .serializers import (
    UserSerializer, KYCSubmissionSerializer, DocumentSerializer,
    KYCDetailSerializer, ChangeStatusSerializer, LoginSerializer,
    NotificationSerializer
)
from .permissions import IsMerchant, IsReviewer, IsOwnerOrReviewer
from .state_machine import validate_transition, StateTransitionError, get_allowed_transitions
from .file_validator import validate_kyc_document, FileValidationError


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """Public API root with quick links for local verification."""
    return Response({
        'message': 'KYC API is running',
        'version': 'v1',
        'auth': {
            'type': 'Token',
            'login': '/api/v1/auth/login/'
        },
        'endpoints': {
            'auth': '/api/v1/auth/',
            'kyc': '/api/v1/kyc/',
            'users': '/api/v1/users/',
            'admin': '/admin/'
        }
    })


class AuthViewSet(viewsets.ViewSet):
    """Authentication endpoints."""
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def login(self, request):
        """
        Login endpoint.
        
        POST /api/v1/auth/login/
        {
            "username": "merchant1",
            "password": "password123"
        }
        
        Returns: token, user details, role
        """
        try:
            serializer = LoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            user = authenticate(
                username=serializer.validated_data['username'],
                password=serializer.validated_data['password']
            )

            if not user:
                return Response(
                    {'error': 'Invalid credentials'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                }
            })
        except Exception as e:
            import traceback
            return Response(
                {'error': str(e), 'traceback': traceback.format_exc()},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def logout(self, request):
        """
        Logout endpoint.
        
        POST /api/v1/auth/logout/
        """
        if request.user and request.user.is_authenticated:
            request.user.auth_token.delete()
        return Response({'message': 'Logged out successfully'})


class KYCSubmissionViewSet(viewsets.ModelViewSet):
    """
    KYC Submission endpoints.
    
    Merchants can:
    - Create new submissions (draft)
    - Update their own draft submissions
    - Submit for review
    - Edit after more_info_requested
    - View their own submissions
    
    Reviewers can:
    - View all submissions
    - Change status (review workflow)
    """
    serializer_class = KYCSubmissionSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReviewer]

    def get_queryset(self):
        """Filter submissions based on user role."""
        user = self.request.user
        if user.role == 'reviewer':
            return KYCSubmission.objects.all()
        elif user.role == 'merchant':
            return KYCSubmission.objects.filter(merchant=user)
        return KYCSubmission.objects.none()

    def get_serializer_class(self):
        """Use detailed serializer for retrieve action."""
        if self.action == 'retrieve':
            return KYCDetailSerializer
        return KYCSubmissionSerializer

    def create(self, request, *args, **kwargs):
        """
        Create new KYC submission (draft).
        
        POST /api/v1/kyc/
        {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+91-9999999999",
            "business_name": "Acme Corp",
            "business_type": "Technology",
            "monthly_volume": 100000.00
        }
        """
        if request.user.role != 'merchant':
            return Response(
                {'error': 'Only merchants can create submissions'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        submission = serializer.save(merchant=request.user, status='draft')

        # Create notification
        Notification.objects.create(
            user=request.user,
            submission=submission,
            event_type='submission_created',
            payload={'action': 'Submission created'}
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """
        Update KYC submission (only draft or after more_info_requested).
        
        PATCH /api/v1/kyc/{id}/
        """
        submission = self.get_object()

        # Merchants can only edit their own submissions
        if request.user.role == 'merchant' and submission.merchant != request.user:
            return Response(
                {'error': 'You can only edit your own submissions'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Can only edit draft or more_info_requested
        if submission.status not in ['draft', 'more_info_requested']:
            return Response(
                {'error': f'Cannot edit submission in "{submission.status}" status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(submission, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsOwnerOrReviewer])
    def upload_document(self, request, pk=None):
        """
        Upload KYC document.
        
        POST /api/v1/kyc/{id}/upload_document/
        
        FormData:
        - document_type: 'pan' | 'aadhaar' | 'bank_statement'
        - file: <file>
        """
        submission = self.get_object()

        # Only merchant can upload documents to their submission
        if request.user.role != 'merchant' or submission.merchant != request.user:
            return Response(
                {'error': 'You can only upload documents to your own submissions'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Can only upload when in draft or more_info_requested
        if submission.status not in ['draft', 'more_info_requested']:
            return Response(
                {'error': f'Cannot upload documents in "{submission.status}" status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        document_type = request.data.get('document_type')
        file_obj = request.FILES.get('file')

        if not document_type or not file_obj:
            return Response(
                {'error': 'document_type and file are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if document_type not in ['pan', 'aadhaar', 'bank_statement']:
            return Response(
                {'error': f'Invalid document_type: {document_type}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate file
        try:
            validate_kyc_document(file_obj)
        except FileValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create or update document
        document, created = Document.objects.update_or_create(
            submission=submission,
            document_type=document_type,
            defaults={'file': file_obj}
        )

        serializer = DocumentSerializer(document)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """
        Submit KYC for review (draft → submitted).
        
        POST /api/v1/kyc/{id}/submit/
        """
        submission = self.get_object()

        if request.user.role != 'merchant' or submission.merchant != request.user:
            return Response(
                {'error': 'You can only submit your own submissions'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate state transition
        try:
            validate_transition(submission.status, 'submitted')
        except StateTransitionError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if all required documents are uploaded
        required_docs = ['pan', 'aadhaar', 'bank_statement']
        uploaded_docs = submission.documents.values_list('document_type', flat=True)
        missing_docs = [doc for doc in required_docs if doc not in uploaded_docs]

        if missing_docs:
            return Response(
                {'error': f'Missing documents: {", ".join(missing_docs)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        submission.status = 'submitted'
        submission.submitted_at = timezone.now()
        submission.save()

        # Create notification for merchant
        Notification.objects.create(
            user=request.user,
            submission=submission,
            event_type='submitted_for_review',
            payload={'action': 'Submission sent for review'}
        )

        serializer = self.get_serializer(submission)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsReviewer])
    def change_status(self, request, pk=None):
        """
        Change submission status (reviewer only).
        
        POST /api/v1/kyc/{id}/change_status/
        {
            "new_status": "approved" | "rejected" | "under_review" | "more_info_requested",
            "reviewer_notes": "Optional notes"
        }
        """
        submission = self.get_object()

        serializer = ChangeStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['new_status']
        reviewer_notes = serializer.validated_data.get('reviewer_notes', '')

        # Validate state transition
        try:
            validate_transition(submission.status, new_status)
        except StateTransitionError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        old_status = submission.status
        submission.status = new_status
        submission.reviewed_at = timezone.now()
        if reviewer_notes:
            submission.reviewer_notes = reviewer_notes
        submission.save()

        # Create notification for merchant
        event_type_map = {
            'approved': 'approved',
            'rejected': 'rejected',
            'more_info_requested': 'more_info_requested',
            'under_review': 'review_started',
        }

        Notification.objects.create(
            user=submission.merchant,
            submission=submission,
            event_type=event_type_map.get(new_status, 'approved'),
            payload={
                'new_status': new_status,
                'old_status': old_status,
                'reviewer_notes': reviewer_notes
            }
        )

        response_serializer = self.get_serializer(submission)
        return Response(response_serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsReviewer])
    def queue(self, request):
        """
        Get submissions in queue (submitted + under_review).
        Ordered by oldest first.
        
        GET /api/v1/kyc/queue/
        
        Returns:
        {
            "queue": [...submissions...],
            "metrics": {
                "total_in_queue": 5,
                "average_time_in_queue_hours": 12.5,
                "approval_rate_7days": 85.5,
                "at_risk_count": 1
            }
        }
        """
        allowed_queue_statuses = ['submitted', 'under_review']
        now = timezone.now()
        threshold = now - timedelta(hours=24)

        # Base queue for overall metrics
        base_queue = KYCSubmission.objects.filter(
            status__in=allowed_queue_statuses
        )

        # Optional filters for reviewer UX
        status_values = request.query_params.get('status')
        search_value = (request.query_params.get('search') or '').strip()
        at_risk_only = request.query_params.get('at_risk_only', 'false').lower() == 'true'
        ordering = request.query_params.get('ordering', 'oldest')

        queue = base_queue

        if status_values:
            requested_statuses = [s.strip() for s in status_values.split(',') if s.strip()]
            valid_statuses = [s for s in requested_statuses if s in allowed_queue_statuses]
            if valid_statuses:
                queue = queue.filter(status__in=valid_statuses)

        if search_value:
            queue = queue.filter(
                Q(name__icontains=search_value)
                | Q(email__icontains=search_value)
                | Q(phone__icontains=search_value)
                | Q(business_name__icontains=search_value)
                | Q(business_type__icontains=search_value)
                | Q(merchant__username__icontains=search_value)
            )

        if at_risk_only:
            queue = queue.filter(submitted_at__lt=threshold)

        ordering_map = {
            'oldest': 'submitted_at',
            'newest': '-submitted_at',
            'high_volume': '-monthly_volume',
            'low_volume': 'monthly_volume',
        }
        queue = queue.order_by(ordering_map.get(ordering, 'submitted_at'))

        serializer = KYCSubmissionSerializer(queue, many=True)

        # Calculate metrics
        total_in_queue = base_queue.count()
        filtered_in_queue = queue.count()

        # Average time in queue
        total_hours = 0
        for submission in base_queue:
            if submission.submitted_at:
                hours = (now - submission.submitted_at).total_seconds() / 3600
                total_hours += hours
        avg_time = total_hours / total_in_queue if total_in_queue > 0 else 0

        # Approval rate (last 7 days)
        seven_days_ago = now - timedelta(days=7)
        approved_7days = KYCSubmission.objects.filter(
            status='approved',
            reviewed_at__gte=seven_days_ago
        ).count()
        total_reviewed_7days = KYCSubmission.objects.filter(
            status__in=['approved', 'rejected'],
            reviewed_at__gte=seven_days_ago
        ).count()
        approval_rate = (approved_7days / total_reviewed_7days * 100) if total_reviewed_7days > 0 else 0

        # At-risk: in queue > 24 hours
        at_risk = base_queue.filter(submitted_at__lt=threshold).count()

        return Response({
            'queue': serializer.data,
            'metrics': {
                'total_in_queue': total_in_queue,
                'filtered_in_queue': filtered_in_queue,
                'average_time_in_queue_hours': round(avg_time, 2),
                'approval_rate_7days': round(approval_rate, 2),
                'at_risk_count': at_risk,
            }
        })

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsMerchant])
    def my_submissions(self, request):
        """
        Get merchant's own submissions.
        
        GET /api/v1/kyc/my_submissions/
        """
        submissions = KYCSubmission.objects.filter(merchant=request.user)
        serializer = KYCSubmissionSerializer(submissions, many=True)
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    """User management endpoints."""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user info."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """Notification endpoints for current user."""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user).select_related('submission')

        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            if is_read.lower() == 'true':
                queryset = queryset.filter(is_read=True)
            elif is_read.lower() == 'false':
                queryset = queryset.filter(is_read=False)

        return queryset

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        updated = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'updated': updated})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=['is_read'])
        return Response({'id': notification.id, 'is_read': notification.is_read})
