"""
Tests for KYC app.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from rest_framework import status
from .models import KYCSubmission, Document, Notification
from .state_machine import validate_transition, StateTransitionError
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class StateTransitionTests(TestCase):
    """Test state machine logic."""

    def test_legal_transition_draft_to_submitted(self):
        """Test that draft -> submitted is allowed."""
        result = validate_transition('draft', 'submitted')
        self.assertTrue(result)

    def test_legal_transition_submitted_to_under_review(self):
        """Test that submitted -> under_review is allowed."""
        result = validate_transition('submitted', 'under_review')
        self.assertTrue(result)

    def test_legal_transition_under_review_to_approved(self):
        """Test that under_review -> approved is allowed."""
        result = validate_transition('under_review', 'approved')
        self.assertTrue(result)

    def test_legal_transition_more_info_to_submitted(self):
        """Test that more_info_requested -> submitted is allowed."""
        result = validate_transition('more_info_requested', 'submitted')
        self.assertTrue(result)

    def test_illegal_transition_approved_to_draft(self):
        """Test that approved -> draft is NOT allowed."""
        with self.assertRaises(StateTransitionError) as context:
            validate_transition('approved', 'draft')
        self.assertIn('Cannot transition', str(context.exception))

    def test_illegal_transition_rejected_to_draft(self):
        """Test that rejected -> draft is NOT allowed."""
        with self.assertRaises(StateTransitionError):
            validate_transition('rejected', 'draft')

    def test_illegal_transition_draft_to_approved(self):
        """Test that draft -> approved is NOT allowed."""
        with self.assertRaises(StateTransitionError):
            validate_transition('draft', 'approved')

    def test_illegal_transition_submitted_to_approved(self):
        """Test that submitted -> approved is NOT allowed (must go through under_review)."""
        with self.assertRaises(StateTransitionError):
            validate_transition('submitted', 'approved')


class KYCSubmissionAPITests(APITestCase):
    """Test KYC submission API endpoints."""

    def setUp(self):
        """Set up test users and data."""
        self.merchant = User.objects.create_user(
            username='merchant1',
            email='merchant1@example.com',
            password='testpass123',
            role='merchant'
        )
        self.merchant_token = Token.objects.create(user=self.merchant)

        self.reviewer = User.objects.create_user(
            username='reviewer1',
            email='reviewer1@example.com',
            password='testpass123',
            role='reviewer'
        )
        self.reviewer_token = Token.objects.create(user=self.reviewer)

    def test_merchant_can_create_submission(self):
        """Test that merchant can create a KYC submission."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.merchant_token.key}')
        
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'phone': '+91-9999999999',
            'business_name': 'Tech Corp',
            'business_type': 'Technology',
            'monthly_volume': '100000.00'
        }
        
        response = self.client.post('/api/v1/kyc/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'draft')
        self.assertEqual(response.data['merchant_username'], 'merchant1')

    def test_merchant_cannot_see_other_submissions(self):
        """Test that merchants can only see their own submissions."""
        merchant2 = User.objects.create_user(
            username='merchant2',
            email='merchant2@example.com',
            password='testpass123',
            role='merchant'
        )
        
        # Create submission for merchant1
        KYCSubmission.objects.create(
            merchant=self.merchant,
            name='John', email='john@example.com', phone='9999999999',
            business_name='Tech', business_type='Tech',
            monthly_volume='100000.00'
        )
        
        # Create submission for merchant2
        KYCSubmission.objects.create(
            merchant=merchant2,
            name='Jane', email='jane@example.com', phone='8888888888',
            business_name='Finance', business_type='Finance',
            monthly_volume='200000.00'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.merchant_token.key}')
        response = self.client.get('/api/v1/kyc/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only see their own submission
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['merchant_username'], 'merchant1')

    def test_reviewer_can_see_all_submissions(self):
        """Test that reviewers can see all submissions."""
        merchant2 = User.objects.create_user(
            username='merchant2',
            email='merchant2@example.com',
            password='testpass123',
            role='merchant'
        )
        
        # Create submissions from different merchants
        KYCSubmission.objects.create(
            merchant=self.merchant,
            name='John', email='john@example.com', phone='9999999999',
            business_name='Tech', business_type='Tech',
            monthly_volume='100000.00'
        )
        
        KYCSubmission.objects.create(
            merchant=merchant2,
            name='Jane', email='jane@example.com', phone='8888888888',
            business_name='Finance', business_type='Finance',
            monthly_volume='200000.00'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.reviewer_token.key}')
        response = self.client.get('/api/v1/kyc/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Reviewer should see all submissions
        self.assertEqual(len(response.data['results']), 2)

    def test_reviewer_can_change_status(self):
        """Test that reviewer can change submission status."""
        submission = KYCSubmission.objects.create(
            merchant=self.merchant,
            status='submitted',
            name='John', email='john@example.com', phone='9999999999',
            business_name='Tech', business_type='Tech',
            monthly_volume='100000.00'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.reviewer_token.key}')
        
        data = {
            'new_status': 'under_review',
            'reviewer_notes': 'Under review'
        }
        
        response = self.client.post(
            f'/api/v1/kyc/{submission.id}/change_status/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'under_review')

    def test_merchant_cannot_change_status(self):
        """Test that merchants cannot change submission status."""
        submission = KYCSubmission.objects.create(
            merchant=self.merchant,
            status='submitted',
            name='John', email='john@example.com', phone='9999999999',
            business_name='Tech', business_type='Tech',
            monthly_volume='100000.00'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.merchant_token.key}')
        
        data = {
            'new_status': 'under_review',
            'reviewer_notes': 'Under review'
        }
        
        response = self.client.post(
            f'/api/v1/kyc/{submission.id}/change_status/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_merchant_cannot_change_status_via_patch(self):
        """Test that merchants cannot directly PATCH status field (state machine bypass)."""
        submission = KYCSubmission.objects.create(
            merchant=self.merchant,
            status='draft',
            name='John', email='john@example.com', phone='9999999999',
            business_name='Tech', business_type='Tech',
            monthly_volume='100000.00'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.merchant_token.key}')
        
        # Try to directly change status via PATCH (should fail - status is read-only)
        response = self.client.patch(
            f'/api/v1/kyc/{submission.id}/',
            {'status': 'approved'},
            format='json'
        )
        
        # Status should NOT be updated (either 400 error or silently ignored)
        submission.refresh_from_db()
        self.assertNotEqual(submission.status, 'approved')
        self.assertEqual(submission.status, 'draft')

    def test_illegal_status_transition_rejected(self):
        """Test that illegal state transitions are rejected with HTTP 400."""
        submission = KYCSubmission.objects.create(
            merchant=self.merchant,
            status='approved',
            name='John', email='john@example.com', phone='9999999999',
            business_name='Tech', business_type='Tech',
            monthly_volume='100000.00'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.reviewer_token.key}')
        
        # Try to transition from approved to draft (illegal)
        data = {
            'new_status': 'draft',
        }
        
        response = self.client.post(
            f'/api/v1/kyc/{submission.id}/change_status/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Cannot transition', response.data['error'])

    def test_only_reviewer_can_access_queue(self):
        """Test that only reviewers can access the queue endpoint."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.merchant_token.key}')
        response = self.client.get('/api/v1/kyc/queue/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.reviewer_token.key}')
        response = self.client.get('/api/v1/kyc/queue/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reviewer_queue_supports_search_and_status_filters(self):
        """Queue endpoint should filter by status and search query."""
        KYCSubmission.objects.create(
            merchant=self.merchant,
            status='submitted',
            submitted_at=timezone.now() - timedelta(hours=2),
            name='Alpha Owner', email='alpha@example.com', phone='9999999999',
            business_name='Alpha Tech', business_type='Tech',
            monthly_volume='100000.00'
        )
        KYCSubmission.objects.create(
            merchant=self.merchant,
            status='under_review',
            submitted_at=timezone.now() - timedelta(hours=3),
            name='Beta Owner', email='beta@example.com', phone='8888888888',
            business_name='Beta Foods', business_type='Food',
            monthly_volume='200000.00'
        )

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.reviewer_token.key}')
        response = self.client.get('/api/v1/kyc/queue/?status=submitted&search=alpha')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['queue']), 1)
        self.assertEqual(response.data['queue'][0]['business_name'], 'Alpha Tech')

    def test_reviewer_queue_supports_at_risk_only(self):
        """Queue endpoint should return only >24h submissions when requested."""
        KYCSubmission.objects.create(
            merchant=self.merchant,
            status='submitted',
            submitted_at=timezone.now() - timedelta(hours=30),
            name='Old Owner', email='old@example.com', phone='7777777777',
            business_name='Old Biz', business_type='Retail',
            monthly_volume='90000.00'
        )
        KYCSubmission.objects.create(
            merchant=self.merchant,
            status='submitted',
            submitted_at=timezone.now() - timedelta(hours=5),
            name='New Owner', email='new@example.com', phone='6666666666',
            business_name='New Biz', business_type='Retail',
            monthly_volume='95000.00'
        )

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.reviewer_token.key}')
        response = self.client.get('/api/v1/kyc/queue/?at_risk_only=true')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['queue']), 1)
        self.assertEqual(response.data['queue'][0]['business_name'], 'Old Biz')


class NotificationAPITests(APITestCase):
    """Test notification endpoints for authenticated users."""

    def setUp(self):
        self.merchant = User.objects.create_user(
            username='merchant_notify',
            email='notify@example.com',
            password='testpass123',
            role='merchant'
        )
        self.other_merchant = User.objects.create_user(
            username='merchant_other',
            email='other@example.com',
            password='testpass123',
            role='merchant'
        )
        self.token = Token.objects.create(user=self.merchant)

        submission = KYCSubmission.objects.create(
            merchant=self.merchant,
            status='draft',
            name='Merchant Owner', email='merchant@example.com', phone='9999991111',
            business_name='Merchant Biz', business_type='Services',
            monthly_volume='120000.00'
        )

        self.unread_notification = Notification.objects.create(
            user=self.merchant,
            submission=submission,
            event_type='submission_created',
            payload={'action': 'created'},
            is_read=False
        )
        Notification.objects.create(
            user=self.merchant,
            submission=submission,
            event_type='submitted_for_review',
            payload={'action': 'submitted'},
            is_read=False
        )
        Notification.objects.create(
            user=self.other_merchant,
            submission=submission,
            event_type='submitted_for_review',
            payload={'action': 'other user'},
            is_read=False
        )

    def test_unread_count_for_current_user(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get('/api/v1/notifications/unread_count/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['unread_count'], 2)

    def test_mark_single_notification_read(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.post(f'/api/v1/notifications/{self.unread_notification.id}/mark_read/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.unread_notification.refresh_from_db()
        self.assertTrue(self.unread_notification.is_read)

    def test_mark_all_notifications_read(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.post('/api/v1/notifications/mark_all_read/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['updated'], 2)
        self.assertEqual(Notification.objects.filter(user=self.merchant, is_read=False).count(), 0)
