# Quick Start Guide

## 30-Second Setup

### Backend
```bash
cd kyc_backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py shell < seed.py
python manage.py runserver
```

### Frontend
```bash
cd kyc_frontend
npm install
npm run dev
```

## Access Application

- Frontend: http://localhost:3000/login
- Admin: http://localhost:8000/admin

## Test Logins

```
merchant1 / merchant123
reviewer1 / reviewer123
admin / (your admin password)
```

## What's Already Set Up

✅ Complete Django project with models  
✅ DRF API with 10+ endpoints  
✅ State machine with validation  
✅ File upload validation (5MB, PDF/JPG/PNG)  
✅ Permission classes (merchant isolation)  
✅ React frontend with routing  
✅ Tailwind CSS styling  
✅ Axios API integration  
✅ Tests (run with: `python manage.py test kyc_app`)  
✅ Seed data (2 merchants + 1 reviewer)  

## Key Files

**Backend**:
- `state_machine.py` - All state transitions
- `file_validator.py` - Upload validation
- `permissions.py` - Role-based access
- `views.py` - API endpoints
- `tests.py` - Test suite

**Frontend**:
- `pages/` - Login, Merchant, Reviewer components
- `context/AuthContext.jsx` - Auth state
- `api.js` - Axios setup

## Common Commands

```bash
# Create migrations
python manage.py makemigrations

# Run tests
python manage.py test kyc_app

# Shell access
python manage.py shell

# Admin panel
http://localhost:8000/admin
```

## Architecture

```
HTTP Request
    ↓
DRF ViewSet (views.py)
    ↓
Permission Check (permissions.py) + Queryset filter
    ↓
Business Logic (state_machine.py, file_validator.py)
    ↓
Database (Django ORM)
    ↓
Serializer (DRF)
    ↓
JSON Response
```

## Frontend Flow

```
Login → Dashboard (role-based)
  ├─ Merchant: Create/Edit KYC, Upload docs
  └─ Reviewer: Queue, Review submissions, Approve/Reject
```

## API Example

```bash
# Get auth token
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"merchant1","password":"merchant123"}'

# Response:
# {"token":"...", "user":{"id":1,"username":"merchant1","role":"merchant"}}

# Create submission
curl -X POST http://localhost:8000/api/v1/kyc/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name":"John",
    "email":"john@business.com",
    "phone":"+91-9999999999",
    "business_name":"Tech Corp",
    "business_type":"Software",
    "monthly_volume":"50000.00"
  }'
```

## Troubleshooting

**CORS Error**: Ensure backend is on `localhost:8000` and frontend on `localhost:3000`  
**Token Error**: Clear localStorage in browser dev tools  
**Migration Error**: Run `python manage.py migrate` from kyc_backend dir  
**File Upload Error**: Check file < 5MB, format is PDF/JPG/PNG  

## Next Steps

1. Test full workflow: Create submission → Upload docs → Submit → Review
2. Check state transitions: Try invalid transitions, verify 400 error
3. Test merchant isolation: Login as merchant2, verify can't see merchant1's data
4. Review code: Check state_machine.py, file_validator.py, permissions.py
5. Run tests: `python manage.py test kyc_app -v 2`
6. Explore admin: http://localhost:8000/admin

## Project Structure

```
kyc_backend/
  ├── manage.py
  ├── requirements.txt
  ├── seed.py
  ├── README.md
  ├── EXPLAINER.md
  ├── db.sqlite3
  ├── kyc_project/
  │   ├── settings.py
  │   ├── urls.py
  │   └── wsgi.py
  └── kyc_app/
      ├── models.py
      ├── views.py
      ├── serializers.py
      ├── permissions.py
      ├── state_machine.py
      ├── file_validator.py
      ├── tests.py
      ├── admin.py
      └── migrations/

kyc_frontend/
  ├── package.json
  ├── vite.config.js
  ├── tailwind.config.js
  ├── index.html
  ├── src/
  │   ├── pages/
  │   ├── components/
  │   ├── context/
  │   ├── api.js
  │   ├── App.jsx
  │   ├── main.jsx
  │   └── index.css
  └── public/
```

## Security Highlights

✅ State machine enforced at API level  
✅ File validation on backend (don't trust frontend)  
✅ Merchant data isolated by queryset + object permissions  
✅ Token authentication on all endpoints  
✅ Clear error messages (no info leakage)  
✅ HTTP 400 for illegal transitions  
✅ HTTP 403 for permission denied  
✅ HTTP 404 for not found (security)  

## Performance

- Database queries optimized with select_related/prefetch_related
- Paginated list endpoints (20 per page)
- Efficient state transition lookup (dict)
- SLA calculation computed on-demand (no background jobs)

---

**Questions?** Check README.md or EXPLAINER.md for detailed documentation.
