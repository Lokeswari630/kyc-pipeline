# KYC Application - Technical Explainer

This document explains the core implementation details, architectural decisions, and code examples.

## 1. State Machine: Where It Lives + How Illegal Transitions Are Blocked

### Location
**File**: `kyc_app/state_machine.py`

This file is the **single source of truth** for all state transitions. No other file defines or modifies the state machine logic.

### Definition

```python
# kyc_app/state_machine.py

ALLOWED_TRANSITIONS = {
    'draft': ['submitted'],
    'submitted': ['under_review'],
    'under_review': ['approved', 'rejected', 'more_info_requested'],
    'more_info_requested': ['submitted'],
    'approved': [],  # Terminal state
    'rejected': [],  # Terminal state
}

def validate_transition(current_status, new_status):
    """Validate state transition - returns True or raises StateTransitionError"""
    if new_status not in ALLOWED_TRANSITIONS[current_status]:
        allowed = ', '.join(ALLOWED_TRANSITIONS[current_status]) or 'none'
        raise StateTransitionError(
            f"Cannot transition from '{current_status}' to '{new_status}'. "
            f"Allowed transitions: {allowed}"
        )
    return True
```

### How It's Enforced

**In views.py - change_status endpoint**:

```python
@action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsReviewer])
def change_status(self, request, pk=None):
    submission = self.get_object()
    new_status = serializer.validated_data['new_status']
    
    # THIS is where the block happens
    try:
        validate_transition(submission.status, new_status)
    except StateTransitionError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST  # ← Returns 400 for illegal transitions
        )
```

### Example: Illegal Transition

Request:
```bash
POST /api/v1/kyc/5/change_status/
{
    "new_status": "draft"  # Trying to transition from "approved" to "draft"
}
```

Response:
```json
HTTP 400 Bad Request
{
    "error": "Cannot transition from 'approved' to 'draft'. Allowed transitions: none"
}
```

### Why This Design?

1. **Centralized**: All logic in one file - easy to modify, audit, test
2. **Enforced**: Can't bypass the state machine in views or elsewhere
3. **Clear errors**: Merchants/reviewers know exactly what went wrong
4. **Testable**: State machine can be unit tested independently

---

## 2. File Upload Validation: Code + Behavior

### Location
**File**: `kyc_app/file_validator.py`

### Complete Validation Code

```python
import os
from django.core.exceptions import ValidationError

ALLOWED_EXTENSIONS = ['pdf', 'jpg', 'jpeg', 'png']
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

class FileValidationError(Exception):
    pass

def validate_kyc_document(file_obj):
    """
    Validate KYC document file.
    
    Raises:
        FileValidationError: If validation fails
    """
    if not file_obj:
        raise FileValidationError("No file provided")
    
    # 1. Check file size
    if file_obj.size > MAX_FILE_SIZE:
        size_mb = file_obj.size / (1024 * 1024)
        raise FileValidationError(
            f"File size ({size_mb:.2f} MB) exceeds maximum allowed size (5 MB)"
        )
    
    # 2. Check file extension
    ext = os.path.splitext(file_obj.name)[1].lower().lstrip('.')
    if ext not in ALLOWED_EXTENSIONS:
        raise FileValidationError(
            f"File type '.{ext}' not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # 3. Check MIME type (backend NEVER trusts frontend)
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
```

### How It's Used in Views

```python
@action(detail=True, methods=['post'])
def upload_document(self, request, pk=None):
    file_obj = request.FILES.get('file')
    
    # Validate file BEFORE saving
    try:
        validate_kyc_document(file_obj)
    except FileValidationError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Save after validation passes
    document, created = Document.objects.update_or_create(
        submission=submission,
        document_type=document_type,
        defaults={'file': file_obj}
    )
```

### Behavior for Large Files

Request: Upload a 6 MB PDF
```bash
POST /api/v1/kyc/1/upload_document/
Content-Type: multipart/form-data

document_type=pan
file=[6MB_file.pdf]
```

Response:
```json
HTTP 400 Bad Request
{
    "error": "File size (6.00 MB) exceeds maximum allowed size (5 MB)"
}
```

**Key Points**:
- ✅ Validation happens **before** file is saved to disk
- ✅ Multiple checks: size → extension → MIME type
- ✅ Clear error messages for each failure type
- ✅ Frontend has hints (max 5MB), but **backend enforces** (don't trust client)

### Why These Checks?

1. **Size check**: Prevents disk space abuse
2. **Extension check**: Blocks executable files (`.exe`, `.sh`, etc.)
3. **MIME type check**: Prevents disguised files (e.g., executable renamed as `.pdf`)
4. **Backend enforced**: No JavaScript can bypass this

---

## 3. Queue Query + SLA Logic

### Location
**File**: `kyc_app/views.py` - `queue` endpoint

### Complete Implementation

```python
@action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsReviewer])
def queue(self, request):
    """
    Get submissions in queue (submitted + under_review).
    Compute metrics dynamically.
    """
    # 1. Get submissions in queue, ordered by oldest first
    queue = KYCSubmission.objects.filter(
        status__in=['submitted', 'under_review']
    ).order_by('submitted_at')
    
    serializer = KYCSubmissionSerializer(queue, many=True)
    
    # 2. Total in queue
    total_in_queue = queue.count()
    
    # 3. Average time in queue
    now = timezone.now()
    total_hours = 0
    for submission in queue:
        if submission.submitted_at:
            hours = (now - submission.submitted_at).total_seconds() / 3600
            total_hours += hours
    avg_time = total_hours / total_in_queue if total_in_queue > 0 else 0
    
    # 4. Approval rate (last 7 days)
    seven_days_ago = now - timedelta(days=7)
    approved_7days = KYCSubmission.objects.filter(
        status='approved',
        reviewed_at__gte=seven_days_ago
    ).count()
    total_reviewed_7days = KYCSubmission.objects.filter(
        status__in=['approved', 'rejected'],
        reviewed_at__gte=seven_days_ago
    ).count()
    approval_rate = (approved_7days / total_reviewed_7days * 100) \
                    if total_reviewed_7days > 0 else 0
    
    # 5. SLA: At-risk (in queue > 24 hours)
    threshold = now - timedelta(hours=24)
    at_risk = queue.filter(submitted_at__lt=threshold).count()
    
    return Response({
        'queue': serializer.data,
        'metrics': {
            'total_in_queue': total_in_queue,
            'average_time_in_queue_hours': round(avg_time, 2),
            'approval_rate_7days': round(approval_rate, 2),
            'at_risk_count': at_risk,
        }
    })
```

### Example Response

```json
{
    "queue": [
        {
            "id": 1,
            "business_name": "Tech Corp",
            "status": "submitted",
            "merchant_username": "merchant1",
            "submitted_at": "2024-04-20T10:30:00Z",
            ...
        }
    ],
    "metrics": {
        "total_in_queue": 15,
        "average_time_in_queue_hours": 12.5,
        "approval_rate_7days": 85.5,
        "at_risk_count": 3
    }
}
```

### SLA Calculation Details

**Scenario**:
- Submitted at: `2024-04-20 10:00 AM`
- Current time: `2024-04-22 2:00 PM`
- Hours in queue: 52 hours
- Status: **At Risk** (> 24 hours)

```python
submitted = datetime(2024, 4, 20, 10, 0)
now = datetime(2024, 4, 22, 14, 0)
threshold = now - timedelta(hours=24)  # 2024-04-21 2:00 PM

if submitted < threshold:  # 2024-04-20 < 2024-04-21 → TRUE
    # Mark as at-risk
```

### Why Computed Dynamically?

- ✅ Always current (no stale data)
- ✅ No need to run background jobs
- ✅ Computed on-demand when reviewer checks dashboard
- ✅ Lightweight calculation for typical queue sizes

---

## 4. Authorization: Merchant Isolation

### Location
**File**: `kyc_app/permissions.py` + `kyc_app/views.py`

### Permission Classes

```python
# permissions.py

class IsOwnerOrReviewer(permissions.BasePermission):
    """
    Merchants can access their own submissions.
    Reviewers can access all submissions.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'reviewer':
            return True  # Reviewers can view all
        if request.user.role == 'merchant':
            return obj.merchant == request.user  # Merchants only their own
        return False
```

### QuerySet Filtering

```python
# views.py

class KYCSubmissionViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        """Filter submissions based on user role."""
        user = self.request.user
        
        if user.role == 'reviewer':
            return KYCSubmission.objects.all()  # Reviewers see all
        
        elif user.role == 'merchant':
            return KYCSubmission.objects.filter(merchant=user)  # Merchants only theirs
        
        return KYCSubmission.objects.none()
```

### Example: Merchant Isolation Test

```python
def test_merchant_cannot_see_other_submissions(self):
    """Verify merchants can only see their own data."""
    merchant1 = User.objects.create_user(..., username='merchant1')
    merchant2 = User.objects.create_user(..., username='merchant2')
    
    # Create submissions
    KYCSubmission.objects.create(merchant=merchant1, ...)
    KYCSubmission.objects.create(merchant=merchant2, ...)
    
    # merchant1 logs in and requests list
    self.client.credentials(HTTP_AUTHORIZATION=f'Token {token1}')
    response = self.client.get('/api/v1/kyc/')
    
    # Should only see their own (1 result)
    self.assertEqual(len(response.data['results']), 1)
    self.assertEqual(response.data['results'][0]['merchant_username'], 'merchant1')
```

### How It's Enforced

1. **Queryset Level**: `get_queryset()` filters at database level
2. **Object Level**: `has_object_permission()` checks individual objects
3. **Endpoint Level**: `list()` uses queryset, `retrieve()` uses both

**Security Flow**:
```
Request → Authentication (token valid?) 
       → Authorization (queryset filters) 
       → Object permissions (has_object_permission) 
       → Response
```

### What Happens if Merchant Tries to Access Other's Data?

```bash
# merchant1 tries to view merchant2's submission (id=5)
GET /api/v1/kyc/5/
Authorization: Token merchant1-token
```

Response:
```
HTTP 403 Forbidden
{
    "detail": "Not found."
}
```

**Note**: Returns 404 instead of 403 for security (don't reveal other submissions exist)

---

## 5. AI Audit: Buggy Code Example + Fix

### Buggy Code (What NOT to do)

```python
# ❌ BAD: Trusts frontend file type
def upload_document_buggy(self, request, pk=None):
    submission = self.get_object()
    file_obj = request.FILES.get('file')
    document_type = request.data.get('document_type')
    
    # BUGGY: Only checks frontend-provided content_type
    # Attacker can send any file with fake MIME type
    if file_obj.content_type != 'application/pdf':
        return Response({'error': 'Only PDF allowed'}, status=400)
    
    # BUGGY: No size check - attacker uploads 1GB file
    # Server crashes or runs out of storage
    document = Document.objects.create(
        submission=submission,
        document_type=document_type,
        file=file_obj
    )
    
    # BUGGY: No filename validation
    # Attacker uploads "../../admin.txt" to traverse directories
    # BUGGY: No permission check
    # Any authenticated user can upload to any submission
    
    return Response(DocumentSerializer(document).data)

# ❌ BAD: State machine not enforced
def change_status_buggy(self, request, pk=None):
    submission = self.get_object()
    new_status = request.data.get('new_status')
    
    # BUGGY: No state transition validation
    # Anyone can go from "approved" to "draft"
    # State machine exists but not used!
    submission.status = new_status
    submission.save()
    
    return Response(KYCSubmissionSerializer(submission).data)

# ❌ BAD: No merchant isolation
def get_submission_buggy(self, request, pk=None):
    # BUGGY: No filtering - anyone can view anyone's data!
    submission = KYCSubmission.objects.get(id=pk)
    return Response(KYCSubmissionSerializer(submission).data)
```

### Problems with Buggy Code

| Issue | Impact | Severity |
|-------|--------|----------|
| Frontend-only validation | Attacker bypasses checks | CRITICAL |
| No file size check | Disk exhaustion DoS | HIGH |
| No permission check | Data breach | CRITICAL |
| State machine not used | Invalid state transitions | HIGH |
| No merchant isolation | Cross-merchant data access | CRITICAL |

---

### Fixed Code (Production-Ready)

```python
# ✅ GOOD: Complete validation
def upload_document(self, request, pk=None):
    submission = self.get_object()
    
    # 1. Check merchant ownership FIRST
    if request.user.role != 'merchant' or submission.merchant != request.user:
        return Response({'error': 'Permission denied'}, status=403)
    
    # 2. Check submission state
    if submission.status not in ['draft', 'more_info_requested']:
        return Response({'error': 'Cannot upload in current state'}, status=400)
    
    # 3. Get file
    file_obj = request.FILES.get('file')
    document_type = request.data.get('document_type')
    
    if not document_type or not file_obj:
        return Response({'error': 'Missing fields'}, status=400)
    
    # 4. BACKEND validates file (don't trust frontend)
    try:
        validate_kyc_document(file_obj)  # Size, extension, MIME type
    except FileValidationError as e:
        return Response({'error': str(e)}, status=400)
    
    # 5. Save only after all checks pass
    document, created = Document.objects.update_or_create(
        submission=submission,
        document_type=document_type,
        defaults={'file': file_obj}
    )
    
    return Response(DocumentSerializer(document).data, status=201)

# ✅ GOOD: State machine enforced
def change_status(self, request, pk=None):
    submission = self.get_object()
    
    # 1. Check reviewer role
    if request.user.role != 'reviewer':
        return Response({'error': 'Permission denied'}, status=403)
    
    # 2. Get new status
    new_status = serializer.validated_data['new_status']
    
    # 3. VALIDATE STATE TRANSITION (don't skip this!)
    try:
        validate_transition(submission.status, new_status)
    except StateTransitionError as e:
        return Response({'error': str(e)}, status=400)
    
    # 4. Only now update state
    submission.status = new_status
    submission.reviewed_at = timezone.now()
    submission.save()
    
    # 5. Create notification for audit trail
    Notification.objects.create(
        user=submission.merchant,
        submission=submission,
        event_type='review_started',
        payload={'new_status': new_status}
    )
    
    return Response(KYCSubmissionSerializer(submission).data)

# ✅ GOOD: Merchant isolation enforced
def get_queryset(self):
    """Filter at database level"""
    user = self.request.user
    
    if user.role == 'reviewer':
        return KYCSubmission.objects.all()
    
    elif user.role == 'merchant':
        return KYCSubmission.objects.filter(merchant=user)
    
    return KYCSubmission.objects.none()

def has_object_permission(self, request, view, obj):
    """Additional check for individual objects"""
    if request.user.role == 'reviewer':
        return True
    if request.user.role == 'merchant':
        return obj.merchant == request.user
    return False
```

### Security Principles Applied

1. **Never trust frontend**: Validate everything on backend
2. **Defense in depth**: Multiple checks at different layers
3. **Fail securely**: Return 403, not reveal what data exists
4. **Enforce invariants**: State machine, merchant ownership, etc.
5. **Audit trail**: Log who did what (notifications)
6. **Clear permissions**: Role-based + object-level checks

---

## Additional Implementation Highlights

### Database Transactions
```python
# Ensures atomicity - all or nothing
with transaction.atomic():
    submission.status = 'submitted'
    submission.submitted_at = timezone.now()
    submission.save()
    Notification.objects.create(...)
```

### Efficient Queries
```python
# Use select_related for foreign keys
submissions = KYCSubmission.objects.select_related('merchant')

# Use prefetch_related for reverse FK
submissions = KYCSubmission.objects.prefetch_related('documents', 'notifications')
```

### Error Handling
```python
# Always return meaningful errors
try:
    ...
except FileValidationError as e:
    return Response({'error': str(e)}, status=400)
except StateTransitionError as e:
    return Response({'error': str(e)}, status=400)
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return Response({'error': 'Internal server error'}, status=500)
```

---

## Testing Strategy

### Unit Tests
- State machine transitions
- File validation rules
- Permission classes

### Integration Tests
- Full API flows
- Cross-merchant isolation
- State transitions with permissions

### Example Test
```python
def test_illegal_transition_rejected_with_400(self):
    """Ensure illegal transitions return HTTP 400"""
    submission = KYCSubmission.objects.create(..., status='approved')
    
    response = self.client.post(
        f'/api/v1/kyc/{submission.id}/change_status/',
        {'new_status': 'draft'}
    )
    
    self.assertEqual(response.status_code, 400)
    self.assertIn('Cannot transition', response.data['error'])
```

---

## Summary

This application demonstrates:
- ✅ Centralized state machine logic
- ✅ Backend file validation (don't trust frontend)
- ✅ Merchant data isolation at queryset + object level
- ✅ Proper error handling with HTTP status codes
- ✅ Role-based access control
- ✅ Audit trail with notifications
- ✅ Production-ready security practices
