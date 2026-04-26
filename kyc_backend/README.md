# KYC Onboarding Pipeline - Full Stack Application

A complete, production-ready KYC (Know Your Customer) onboarding system built with Django, Django REST Framework, and React.

## Table of Contents

- [Tech Stack](#tech-stack)
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation & Setup](#installation--setup)
- [Running the Application](#running-the-application)
- [API Endpoints](#api-endpoints)
- [User Roles](#user-roles)
- [State Machine](#state-machine)
- [Testing](#testing)

## Tech Stack

### Backend
- **Framework**: Django 4.2
- **API**: Django REST Framework 3.14
- **Database**: SQLite3
- **Authentication**: Token-based (DRF Token)
- **CORS**: django-cors-headers

### Frontend
- **Library**: React 18
- **Build Tool**: Vite
- **CSS**: Tailwind CSS
- **HTTP Client**: Axios
- **Routing**: React Router v6

## Features

### 1. User Roles
- **Merchant**: Create and manage KYC submissions
- **Reviewer**: Review submissions and approve/reject

### 2. KYC Submission Workflow
- **Multi-step form**: Personal + Business Information
- **Document upload**: PAN, Aadhaar, Bank Statement
- **Draft saving**: Save work in progress
- **Submit for review**: Move to reviewer queue
- **Edit capability**: Modify draft or after "more info requested"

### 3. State Machine
Strict state transitions enforced:
```
draft → submitted → under_review → {approved|rejected|more_info_requested}
more_info_requested → submitted
```

### 4. Reviewer Dashboard
- Queue view (submitted + under_review)
- Metrics: Queue count, avg time, approval rate, at-risk count
- SLA tracking: Flag submissions > 24h in queue
- Bulk actions: Approve, reject, request info

### 5. File Upload
- Supported formats: PDF, JPG, PNG
- Max size: 5 MB
- Backend validation
- Backend MIME type check

### 6. Notifications
- Event-based: submission_created, submitted_for_review, review_started, etc.
- Stored in database with timestamps and payload

---

## Project Structure

```
kyc_backend/
├── kyc_project/              # Django project settings
│   ├── settings.py          # Configuration
│   ├── urls.py              # Root URL routing
│   ├── wsgi.py
│   └── __init__.py
├── kyc_app/                 # Main application
│   ├── models.py            # Database models
│   ├── views.py             # DRF ViewSets
│   ├── serializers.py       # DRF Serializers
│   ├── urls.py              # App routing
│   ├── permissions.py       # Authorization classes
│   ├── state_machine.py     # State transition logic
│   ├── file_validator.py    # File upload validation
│   ├── admin.py             # Admin interface
│   ├── apps.py
│   ├── tests.py             # Test suite
│   └── __init__.py
├── manage.py                # Django management
├── seed.py                  # Seed data script
├── requirements.txt         # Dependencies
├── db.sqlite3              # Database (auto-created)
└── media/                  # Uploaded files

kyc_frontend/
├── src/
│   ├── pages/              # Page components
│   │   ├── Login.jsx
│   │   ├── MerchantDashboard.jsx
│   │   ├── MerchantForm.jsx
│   │   ├── MerchantSubmissionDetail.jsx
│   │   ├── ReviewerDashboard.jsx
│   │   └── ReviewerSubmissionDetail.jsx
│   ├── components/         # Reusable components
│   │   └── ProtectedRoute.jsx
│   ├── context/            # React context
│   │   └── AuthContext.jsx
│   ├── api.js             # Axios instance & API calls
│   ├── App.jsx            # Main router
│   ├── main.jsx           # Entry point
│   └── index.css          # Global styles
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
└── .env.example
```

---

## Installation & Setup

### Prerequisites
- Python 3.9+
- Node.js 16+
- npm or yarn

### Backend Setup

1. **Navigate to backend**
   ```bash
   cd kyc_backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser (admin)**
   ```bash
   python manage.py createsuperuser
   # Username: admin
   # Email: admin@example.com
   # Password: (enter password)
   ```

6. **Load seed data**
   ```bash
   python manage.py shell < seed.py
   ```

### Frontend Setup

1. **Navigate to frontend**
   ```bash
   cd kyc_frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Create .env file**
   ```bash
   cp .env.example .env
   ```
   (Default API URL is already set in api.js)

---

## Running the Application

### Start Backend

```bash
cd kyc_backend
source venv/bin/activate
python manage.py runserver
```

Backend runs on: `http://localhost:8000`

### Start Frontend

```bash
cd kyc_frontend
npm run dev
```

Frontend runs on: `http://localhost:3000`

### Access Application

1. **Frontend**: http://localhost:3000/login
2. **Admin Panel**: http://localhost:8000/admin

### Test Credentials

```
Merchant User:
  Username: merchant1
  Password: merchant123

Reviewer User:
  Username: reviewer1
  Password: reviewer123

Admin:
  Username: admin
  Password: (your admin password)
```

---

## API Endpoints

All endpoints use Token Authentication and return JSON.

### Authentication
- `POST /api/v1/auth/login/` - Login and get token
- `POST /api/v1/auth/logout/` - Logout

### KYC Submissions
- `GET /api/v1/kyc/` - List submissions (merchant: own, reviewer: all)
- `POST /api/v1/kyc/` - Create new submission (merchant only)
- `GET /api/v1/kyc/{id}/` - Get submission details
- `PATCH /api/v1/kyc/{id}/` - Update submission (draft/more_info_requested only)
- `POST /api/v1/kyc/{id}/upload_document/` - Upload document
- `POST /api/v1/kyc/{id}/submit/` - Submit for review
- `POST /api/v1/kyc/{id}/change_status/` - Change status (reviewer only)
- `GET /api/v1/kyc/queue/` - Get queue with metrics (reviewer only)
- `GET /api/v1/kyc/my_submissions/` - Get merchant's own submissions

### Users
- `GET /api/v1/users/me/` - Get current user info

---

## User Roles

### Merchant
✅ Create new KYC submissions  
✅ Edit draft submissions  
✅ Upload documents  
✅ Submit for review  
✅ View own submissions  
✅ Edit after "more info requested"  
❌ Cannot see other merchants' data  
❌ Cannot review submissions  

### Reviewer
✅ View all submissions  
✅ See queue with metrics  
✅ Change submission status  
✅ Approve/Reject/Request info  
❌ Cannot create submissions  
❌ Cannot edit submissions  

---

## State Machine

### States
1. **draft** - Initial state, merchant can edit
2. **submitted** - Sent for review, moved to queue
3. **under_review** - Reviewer is examining
4. **approved** - Final approved state
5. **rejected** - Final rejected state
6. **more_info_requested** - Merchant must resubmit

### Legal Transitions
```
draft → submitted
submitted → under_review
under_review → approved
under_review → rejected
under_review → more_info_requested
more_info_requested → submitted
```

### Implementation
- Centralized in `kyc_app/state_machine.py`
- Enforced in `views.py` before state change
- Returns HTTP 400 with clear error message for illegal transitions

---

## File Upload Validation

### Rules
- **Formats**: PDF, JPG, JPEG, PNG
- **Max Size**: 5 MB
- **Validation**: Backend only (frontend hint only)
- **Check MIME type**: Yes
- **Required Documents**: All three (PAN, Aadhaar, Bank Statement)

### Backend Validation Code

```python
# kyc_app/file_validator.py
def validate_kyc_document(file_obj):
    if file_obj.size > 5 * 1024 * 1024:
        raise FileValidationError("File size exceeds 5 MB")
    
    ext = os.path.splitext(file_obj.name)[1].lower().lstrip('.')
    if ext not in ['pdf', 'jpg', 'jpeg', 'png']:
        raise FileValidationError(f"File type '.{ext}' not allowed")
    
    if file_obj.content_type not in [
        'application/pdf', 'image/jpeg', 'image/png'
    ]:
        raise FileValidationError("Invalid MIME type")
```

---

## SLA Tracking

### Logic
- Computed dynamically (not stored)
- Flag submissions > 24 hours in queue
- Available in reviewer queue metrics

### Calculation

```python
# views.py - queue endpoint
threshold = now - timedelta(hours=24)
at_risk = queue.filter(submitted_at__lt=threshold).count()
```

---

## Notifications

Stored for every state change:

```python
# Notification model
- user_id: Who receives the notification
- submission_id: Related submission
- event_type: submission_created, submitted_for_review, etc.
- payload: JSON data
- created_at: Timestamp
- is_read: Boolean flag
```

---

## Testing

### Run Tests

```bash
cd kyc_backend
python manage.py test kyc_app.tests -v 2
```

### Test Coverage

✅ Legal state transitions  
✅ Illegal state transitions (rejected with HTTP 400)  
✅ Merchant data isolation  
✅ Reviewer can see all  
✅ File upload validation  
✅ Permission enforcement  

### Example Test: Illegal Transition

```python
def test_illegal_transition_approved_to_draft(self):
    """Test that approved → draft is NOT allowed."""
    with self.assertRaises(StateTransitionError) as context:
        validate_transition('approved', 'draft')
    self.assertIn('Cannot transition', str(context.exception))
```

---

## Admin Panel

Django admin interface available at `/admin`:

- View all submissions
- View users and roles
- View notifications
- View documents
- Filter by status, date, merchant

---

## Error Handling

### Standard Error Response

```json
{
  "error": "Description of the error"
}
```

### Common Errors

- `400 Bad Request` - Invalid state transition, file too large, missing required fields
- `401 Unauthorized` - Invalid credentials or missing token
- `403 Forbidden` - Insufficient permissions (merchant viewing other's data, etc.)
- `404 Not Found` - Submission not found

---

## Database Models

### User
```
- id
- username (unique)
- email
- role: 'merchant' | 'reviewer'
- is_staff, is_active, etc. (standard Django)
```

### KYCSubmission
```
- id
- merchant (FK to User)
- status (state machine states)
- name, email, phone
- business_name, business_type, monthly_volume
- created_at, updated_at, submitted_at, reviewed_at
- reviewer_notes
```

### Document
```
- id
- submission (FK)
- document_type: 'pan' | 'aadhaar' | 'bank_statement'
- file (FileField with validation)
- uploaded_at
```

### Notification
```
- id
- user (FK)
- submission (FK)
- event_type
- payload (JSON)
- created_at
- is_read
```

---

## Deployment Notes

### Before Production

1. Change `DEBUG = False` in settings.py
2. Set strong `SECRET_KEY`
3. Configure `ALLOWED_HOSTS`
4. Use PostgreSQL instead of SQLite
5. Set up proper CORS origins
6. Enable HTTPS
7. Use environment variables for secrets

### Environment Variables

```bash
DEBUG=False
SECRET_KEY=your-secure-key
ALLOWED_HOSTS=yourdomain.com
DATABASE_URL=postgresql://...
CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

---

## Support & Troubleshooting

### CORS Issues
- Ensure `localhost:3000` is in `CORS_ALLOWED_ORIGINS`
- Check backend is running on `localhost:8000`

### Database Issues
- Run migrations: `python manage.py migrate`
- Clear migrations if needed: `python manage.py migrate kyc_app zero`

### Token Expiration
- Token is stored in localStorage
- Manual logout clears token

### File Upload Issues
- Check file size < 5 MB
- Verify file format (PDF/JPG/PNG)
- Check media folder permissions

---

## License

MIT License - Feel free to use and modify as needed.
