# API Endpoints Reference

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication

### Login
```
POST /auth/login/
Content-Type: application/json

{
  "username": "merchant1",
  "password": "merchant123"
}

Response:
{
  "token": "abc123...",
  "user": {
    "id": 1,
    "username": "merchant1",
    "email": "merchant1@example.com",
    "role": "merchant"
  }
}
```

### Logout
```
POST /auth/logout/
Authorization: Token abc123...
```

---

## KYC Submissions

### List Submissions
```
GET /kyc/
Authorization: Token abc123...

- Merchants: See only their own submissions
- Reviewers: See all submissions

Response:
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "merchant_username": "merchant1",
      "status": "draft",
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "+91-9999999999",
      "business_name": "Tech Corp",
      "business_type": "Software",
      "monthly_volume": "50000.00",
      "documents": [],
      "created_at": "2024-04-20T10:30:00Z",
      "updated_at": "2024-04-20T10:30:00Z",
      "submitted_at": null,
      "reviewed_at": null,
      "reviewer_notes": null,
      "allowed_transitions": ["submitted"]
    }
  ]
}
```

### Create Submission (Draft)
```
POST /kyc/
Authorization: Token abc123...
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+91-9999999999",
  "business_name": "Tech Corp",
  "business_type": "Software",
  "monthly_volume": "50000.00"
}

Response: 201 Created
(Same structure as list response)
```

### Get Submission Details
```
GET /kyc/{id}/
Authorization: Token abc123...

Response: 200 OK
(Extended response with documents and notifications)
```

### Update Submission
```
PATCH /kyc/{id}/
Authorization: Token abc123...
Content-Type: application/json

{
  "name": "Jane Doe",
  "phone": "+91-8888888888"
}

- Can only update if status is "draft" or "more_info_requested"
- Merchants can only update their own
- Reviewers cannot update

Response: 200 OK
```

### Upload Document
```
POST /kyc/{id}/upload_document/
Authorization: Token abc123...
Content-Type: multipart/form-data

Form Fields:
- document_type: "pan" | "aadhaar" | "bank_statement"
- file: <binary file>

Allowed: PDF, JPG, PNG (Max 5 MB)

Response: 201 Created or 200 OK
{
  "id": 1,
  "document_type": "pan",
  "file": "/media/kyc_documents/2024/04/20/pan_abc123.pdf",
  "uploaded_at": "2024-04-20T10:30:00Z"
}

Errors:
- 400: File too large, invalid format, invalid MIME type
- 400: Cannot upload in current submission status
```

### Submit for Review
```
POST /kyc/{id}/submit/
Authorization: Token abc123...

- Transition: draft → submitted
- All 3 documents must be uploaded
- Merchants only (cannot call as reviewer)
- Creates notification for merchant

Response: 200 OK
{
  "id": 1,
  "status": "submitted",
  "submitted_at": "2024-04-20T10:35:00Z",
  ...
}

Errors:
- 400: Missing required documents
- 400: Invalid state transition
- 403: Not your submission
```

### Change Status (Reviewer Only)
```
POST /kyc/{id}/change_status/
Authorization: Token abc123...
Content-Type: application/json

{
  "new_status": "approved" | "rejected" | "under_review" | "more_info_requested",
  "reviewer_notes": "Optional review notes"
}

Valid Transitions:
- submitted → under_review
- under_review → approved
- under_review → rejected
- under_review → more_info_requested

Response: 200 OK
(Updated submission)

Errors:
- 400: Invalid state transition (e.g., approved → draft)
- 403: Only reviewers can call this
- 404: Submission not found
```

### Get Queue (Reviewer Only)
```
GET /kyc/queue/
Authorization: Token abc123...

Returns submissions in queue (submitted + under_review) ordered by oldest first

Response: 200 OK
{
  "queue": [
    {
      "id": 1,
      "merchant_username": "merchant1",
      "status": "submitted",
      "business_name": "Tech Corp",
      "name": "John Doe",
      "email": "john@example.com",
      "submitted_at": "2024-04-20T08:00:00Z",
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

At-Risk: Submissions > 24 hours in queue
```

### Get Own Submissions (Merchant Only)
```
GET /kyc/my_submissions/
Authorization: Token abc123...

Response: 200 OK
(List of merchant's submissions)
```

---

## Users

### Get Current User
```
GET /users/me/
Authorization: Token abc123...

Response: 200 OK
{
  "id": 1,
  "username": "merchant1",
  "email": "merchant1@example.com",
  "role": "merchant"
}
```

---

## Error Responses

### Standard Error Format
```json
{
  "error": "Description of what went wrong"
}
```

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | GET request |
| 201 | Created | POST /kyc/ |
| 400 | Bad Request | Invalid transition, missing field |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Merchant viewing other's data |
| 404 | Not Found | Submission doesn't exist |
| 500 | Server Error | Unexpected error |

### Common Error Examples

**Missing Token**
```
GET /kyc/
Response: 401
{
  "detail": "Authentication credentials were not provided."
}
```

**Illegal State Transition**
```
POST /kyc/1/change_status/
{"new_status": "draft"}

Response: 400
{
  "error": "Cannot transition from 'approved' to 'draft'. Allowed transitions: none"
}
```

**File Too Large**
```
POST /kyc/1/upload_document/
(6 MB file)

Response: 400
{
  "error": "File size (6.00 MB) exceeds maximum allowed size (5 MB)"
}
```

**Merchant Isolation**
```
GET /kyc/5/  (another merchant's submission)

Response: 404 (Security: don't reveal it exists)
{
  "detail": "Not found."
}
```

---

## Pagination

List endpoints support pagination:

```
GET /kyc/?page=1

Response:
{
  "count": 100,
  "next": "http://localhost:8000/api/v1/kyc/?page=2",
  "previous": null,
  "results": [...]
}
```

Page size: 20 items

---

## Filtering & Ordering

List endpoints support basic filtering:

```
GET /kyc/?search=tech  # Search by business_name or email
```

---

## Testing with cURL

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"merchant1","password":"merchant123"}' | jq -r '.token')

# 2. Create submission
curl -X POST http://localhost:8000/api/v1/kyc/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name":"John",
    "email":"john@business.com",
    "phone":"+91-9999999999",
    "business_name":"Tech Corp",
    "business_type":"Software",
    "monthly_volume":"50000"
  }'

# 3. Upload document
curl -X POST http://localhost:8000/api/v1/kyc/1/upload_document/ \
  -H "Authorization: Token $TOKEN" \
  -F "document_type=pan" \
  -F "file=@/path/to/pan.pdf"

# 4. Submit for review
curl -X POST http://localhost:8000/api/v1/kyc/1/submit/ \
  -H "Authorization: Token $TOKEN"

# 5. As reviewer: Get queue
TOKEN_REVIEWER=$(curl -s -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"reviewer1","password":"reviewer123"}' | jq -r '.token')

curl -X GET http://localhost:8000/api/v1/kyc/queue/ \
  -H "Authorization: Token $TOKEN_REVIEWER"

# 6. Approve submission
curl -X POST http://localhost:8000/api/v1/kyc/1/change_status/ \
  -H "Authorization: Token $TOKEN_REVIEWER" \
  -H "Content-Type: application/json" \
  -d '{"new_status":"under_review"}'

curl -X POST http://localhost:8000/api/v1/kyc/1/change_status/ \
  -H "Authorization: Token $TOKEN_REVIEWER" \
  -H "Content-Type: application/json" \
  -d '{"new_status":"approved","reviewer_notes":"Looks good!"}'
```

---

## Webhook Events (Future)

Currently events are stored in Notification model. Future can trigger webhooks:

```
POST {client_webhook_url}
{
  "event": "submission.submitted",
  "submission_id": 1,
  "status": "submitted",
  "timestamp": "2024-04-20T10:35:00Z"
}
```

---

## Rate Limiting (Future)

Implement with `django-ratelimit`:

```
GET /api/v1/kyc/ - Max 100 requests/hour
POST /api/v1/kyc/{id}/upload_document/ - Max 10 requests/hour
```

---

## API Versioning

All endpoints use `/api/v1/` prefix.

Future versions will use:
```
/api/v2/
/api/v3/
```

Previous versions will maintain backward compatibility for 2 releases.
