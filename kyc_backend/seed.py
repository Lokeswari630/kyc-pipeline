"""
Seed script to create test data for KYC application.

Run with: python manage.py shell < seed.py
"""

from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from kyc_app.models import KYCSubmission, Document, Notification

User = get_user_model()

# Clear existing data (optional)
print("Clearing existing data...")
User.objects.all().delete()

print("Creating users...")

# Create merchant 1 with draft submission
merchant1 = User.objects.create_user(
    username='merchant1',
    email='merchant1@example.com',
    password='merchant123',
    role='merchant'
)
print(f"✓ Created merchant: {merchant1.username}")

# Create merchant 2 with under_review submission
merchant2 = User.objects.create_user(
    username='merchant2',
    email='merchant2@example.com',
    password='merchant123',
    role='merchant'
)
print(f"✓ Created merchant: {merchant2.username}")

# Create reviewer
reviewer = User.objects.create_user(
    username='reviewer1',
    email='reviewer1@example.com',
    password='reviewer123',
    role='reviewer'
)
print(f"✓ Created reviewer: {reviewer.username}")

print("\nCreating KYC submissions...")

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
print(f"✓ Created draft submission for {merchant1.username}: {submission1.id}")

# Create notification for submission1
Notification.objects.create(
    user=merchant1,
    submission=submission1,
    event_type='submission_created',
    payload={'action': 'Draft submission created'}
)

# Merchant 2 - Under Review submission
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
print(f"✓ Created submitted submission for {merchant2.username}: {submission2.id}")

Notification.objects.create(
    user=merchant2,
    submission=submission2,
    event_type='submitted_for_review',
    payload={'action': 'Submission sent for review'}
)

print("\n✓ Seed data created successfully!")
print("\n" + "="*50)
print("TEST CREDENTIALS")
print("="*50)
print(f"\nMerchant 1:")
print(f"  Username: merchant1")
print(f"  Password: merchant123")
print(f"  Status: Has draft submission")

print(f"\nMerchant 2:")
print(f"  Username: merchant2")
print(f"  Password: merchant123")
print(f"  Status: Has submitted submission")

print(f"\nReviewer:")
print(f"  Username: reviewer1")
print(f"  Password: reviewer123")

print("\n" + "="*50)
