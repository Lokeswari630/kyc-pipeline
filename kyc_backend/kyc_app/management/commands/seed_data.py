"""
Django management command to seed database with test data.
Usage: python manage.py seed_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from kyc_app.models import KYCSubmission, Document, Notification

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed database with test data for KYC application'

    def handle(self, *args, **options):
        # Check if data already exists
        if User.objects.filter(username='merchant1').exists():
            self.stdout.write(self.style.WARNING('⚠️  Test data already exists. Skipping...'))
            return

        self.stdout.write(self.style.SUCCESS('Creating seed data...'))

        # Create merchant 1
        merchant1 = User.objects.create_user(
            username='merchant1',
            email='merchant1@example.com',
            password='merchant123',
            role='merchant'
        )
        self.stdout.write(f"✓ Created merchant: {merchant1.username}")

        # Create merchant 2
        merchant2 = User.objects.create_user(
            username='merchant2',
            email='merchant2@example.com',
            password='merchant123',
            role='merchant'
        )
        self.stdout.write(f"✓ Created merchant: {merchant2.username}")

        # Create reviewer
        reviewer = User.objects.create_user(
            username='reviewer1',
            email='reviewer1@example.com',
            password='reviewer123',
            role='reviewer'
        )
        self.stdout.write(f"✓ Created reviewer: {reviewer.username}")

        # Merchant 1 - Draft submission
        submission1 = KYCSubmission.objects.create(
            merchant=merchant1,
            status='draft',
            name='Alice Johnson',
            email='alice@business1.com',
            phone='+91-9876543210',
            business_name='Tech Startup Inc',
            business_type='Software Development',
            monthly_volume='50000.00'
        )
        self.stdout.write(f"✓ Created draft submission (ID: {submission1.id})")

        Notification.objects.create(
            user=merchant1,
            submission=submission1,
            event_type='submission_created',
            payload={'action': 'Draft submission created'}
        )

        # Merchant 2 - Submitted (in queue)
        submission2 = KYCSubmission.objects.create(
            merchant=merchant2,
            status='submitted',
            name='Bob Smith',
            email='bob@business2.com',
            phone='+91-8765432109',
            business_name='Finance Solutions Ltd',
            business_type='Financial Services',
            monthly_volume='150000.00',
            submitted_at=timezone.now() - timedelta(hours=5)
        )
        self.stdout.write(f"✓ Created submitted submission (ID: {submission2.id})")

        Notification.objects.create(
            user=merchant2,
            submission=submission2,
            event_type='submitted_for_review',
            payload={'action': 'Submission sent for review'}
        )

        # Print credentials
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('✅ TEST CREDENTIALS'))
        self.stdout.write('='*60)
        self.stdout.write('\nMerchant 1 (Has draft submission):')
        self.stdout.write('  Username: merchant1')
        self.stdout.write('  Password: merchant123')
        self.stdout.write('  Email: merchant1@example.com')
        self.stdout.write('\nMerchant 2 (Has submitted submission - in review queue):')
        self.stdout.write('  Username: merchant2')
        self.stdout.write('  Password: merchant123')
        self.stdout.write('  Email: merchant2@example.com')
        self.stdout.write('\nReviewer (Can review all submissions):')
        self.stdout.write('  Username: reviewer1')
        self.stdout.write('  Password: reviewer123')
        self.stdout.write('  Email: reviewer1@example.com')
        self.stdout.write('='*60 + '\n')
