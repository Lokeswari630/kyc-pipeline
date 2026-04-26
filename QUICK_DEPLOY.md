# 🚀 COPY-PASTE DEPLOY INSTRUCTIONS

Choose your platform below and follow the exact steps.

---

## 🎯 RENDER (Recommended - Easiest)

### Prerequisites
- GitHub account with code pushed
- Render account (free at render.com)

### Step-by-Step

1. **Login to Render**
   ```
   Go to https://render.com
   Click "Sign in with GitHub"
   Authorize Render
   ```

2. **Create Backend Service**
   ```
   Click "Create +" → "Web Service"
   Connect GitHub repo (choose kyc-app)
   Name: kyc-backend
   Region: Oregon or closest to you
   Branch: main
   Runtime: Python 3.11
   ```

3. **Set Build Command**
   ```
   cd kyc_backend && pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate && python manage.py seed_data
   ```

4. **Set Start Command**
   ```
   cd kyc_backend && gunicorn kyc_project.wsgi:application --log-file -
   ```

5. **Select Plan**
   ```
   Choose: Free
   Auto-spin down: Enable (saves resources)
   ```

6. **Add Environment Variables**
   ```
   Click "Environment"
   SECRET_KEY → Leave blank (Render will generate)
   DEBUG → false
   USE_POSTGRES → true
   DATABASE_URL → Leave blank (auto-linked)
   ALLOWED_HOSTS → kyc-backend-XXXXX.onrender.com
   CORS_ALLOWED_ORIGINS → Will set after frontend deployment
   ```

7. **Deploy**
   ```
   Click "Deploy"
   Wait 2-3 minutes
   Check logs for "Seed data created" ✓
   ```

8. **Get Backend URL**
   ```
   After deploy: https://kyc-backend-XXXXX.onrender.com
   Save this URL
   ```

9. **Create Frontend Service**
   ```
   Click "Create +" → "Static Site"
   Connect same GitHub repo
   Name: kyc-frontend
   Branch: main
   Build Command: cd kyc_frontend && npm install && npm run build
   Publish Directory: kyc_frontend/dist
   ```

10. **Add Frontend Environment Variables**
    ```
    Click "Environment"
    VITE_API_URL → https://kyc-backend-XXXXX.onrender.com/api/v1
    ```

11. **Deploy Frontend**
    ```
    Click "Deploy"
    Wait 1-2 minutes
    ```

### Your URLs
```
Frontend: https://kyc-frontend-XXXXX.onrender.com
Backend: https://kyc-backend-XXXXX.onrender.com

UPDATE: Go back to backend environment variables
CORS_ALLOWED_ORIGINS → https://kyc-frontend-XXXXX.onrender.com
Click "Save"
```

### Test It
```
1. Open https://kyc-frontend-XXXXX.onrender.com
2. Click "Sign In"
3. Username: merchant1
4. Password: merchant123
5. Dashboard loads → You're live! 🎉
```

---

## 🚂 RAILWAY (Alternative - Very Easy)

### Prerequisites
- GitHub account with code pushed
- Railway account (free at railway.app)

### Step-by-Step

1. **Login to Railway**
   ```
   Go to https://railway.app
   Click "Login with GitHub"
   Authorize Railway
   ```

2. **Create Project**
   ```
   Click "Create New Project"
   Click "Deploy from GitHub repo"
   Select your kyc-app repository
   ```

3. **Railway Auto-Configures**
   ```
   Detects Django automatically
   Creates PostgreSQL database
   Adds environment variables
   ```

4. **Verify Variables**
   ```
   Click "Configure"
   Should show:
   - DATABASE_URL (auto-set)
   - RAILWAY_ENVIRONMENT_NAME
   ```

5. **Add Missing Variables**
   ```
   Click the "+" to add variable
   SECRET_KEY → Generate a random strong string
   DEBUG → false
   USE_POSTGRES → true
   CORS_ALLOWED_ORIGINS → Will update after frontend
   ```

6. **Deploy**
   ```
   Select Service → View Logs
   Look for: "✅ TEST CREDENTIALS"
   Deploy should succeed in 1-2 minutes
   ```

7. **Get URLs**
   ```
   Backend URL appears in Railway dashboard
   Save it
   ```

8. **Deploy Frontend** (Same Repo)
   ```
   In Railway dashboard, create new service
   Choose "GitHub repo" (same one)
   Select root directory (not needed, auto-detects)
   Build: cd kyc_frontend && npm install && npm run build
   Start: npm run preview
   ```

9. **Add Frontend Variables**
   ```
   VITE_API_URL → https://your-backend-railway-url/api/v1
   ```

### Test It
```
Open your frontend URL
Login: merchant1 / merchant123
```

---

## 🪰 FLY.IO (More Advanced)

### Prerequisites
- GitHub account
- Fly.io account (free at fly.io)
- Fly CLI installed: `curl -L https://fly.io/install.sh | sh`

### Commands
```bash
# Install
curl -L https://fly.io/install.sh | sh

# Login
fly auth login
# Opens browser, authenticate with GitHub

# In project root
cd /path/to/kyc-app

# Create app (auto-generates fly.toml)
fly launch
# Answers:
# - App name: kyc-app (or your choice)
# - Region: Choose closest
# - Database: Yes, create Postgres
# - Deploy: No (we'll customize first)

# Edit fly.toml - Add build command
# [build]
# cmd = "cd kyc_backend && python manage.py migrate && python manage.py seed_data"

# Set env vars
fly secrets set SECRET_KEY=your-secret-key
fly secrets set DEBUG=false
fly secrets set USE_POSTGRES=true

# Deploy
fly deploy

# Get URL
fly apps open kyc-backend
# Shows: https://kyc-app-XXX.fly.dev
```

---

## 🐋 KOYEB (Nice Alternative)

### Prerequisites
- GitHub account
- Koyeb account (free at koyeb.com)

### Steps
```
1. Go to koyeb.com → Sign up
2. Click "Create Service" → "GitHub"
3. Select your repository
4. Fill in:
   - Service name: kyc-backend
   - Build command: cd kyc_backend && pip install -r requirements.txt && python manage.py migrate && python manage.py seed_data
   - Start command: cd kyc_backend && gunicorn kyc_project.wsgi:application
5. Add env vars (same as Render)
6. Deploy
7. Repeat for frontend as static site
```

---

## ✅ POST-DEPLOYMENT CHECKLIST

- [ ] Backend deployed and running
- [ ] Frontend deployed and running
- [ ] Can access frontend URL in browser
- [ ] Can login with merchant1/merchant123
- [ ] Dashboard loads without errors
- [ ] Create new submission works
- [ ] Can logout and login as reviewer1/reviewer123
- [ ] Reviewer can see queue
- [ ] All features working

---

## 🔑 YOUR CREDENTIALS

```
SAVE THESE SOMEWHERE SAFE

MERCHANT 1
Username: merchant1
Password: merchant123

MERCHANT 2  
Username: merchant2
Password: merchant123

REVIEWER
Username: reviewer1
Password: reviewer123

ADMIN (for Django admin - set your own)
Create: python manage.py createsuperuser (after deployed)
```

---

## 🆘 QUICK TROUBLESHOOTING

### Can't login
- Wait 30 seconds after deployment (seed data might still be running)
- Check seed_data command ran in logs: "✅ TEST CREDENTIALS"

### Frontend shows "Cannot reach API"
- Check VITE_API_URL is set to your backend URL + `/api/v1`
- Try opening backend URL directly in browser to test

### Database error
- Check PostgreSQL env var is set
- Restart service (kill and redeploy)

### Build fails
- Read full error log
- Ensure requirements.txt has all packages
- Check build command has `--noinput` for prompts

---

## 📝 WHAT YOU JUST DEPLOYED

✅ Django REST API with PostgreSQL
✅ React frontend with Vite
✅ Token authentication
✅ KYC submission workflow
✅ File upload (PDF/JPG/PNG)
✅ Reviewer queue & approval flow
✅ Notifications system
✅ Test data auto-seeded
✅ Production security configured

## 🎉 YOU'RE LIVE!

Share these URLs:
```
Frontend: https://your-frontend-url.com
Backend API: https://your-backend-url.com/api/v1
Admin: https://your-backend-url.com/admin
```

Test credentials above! 🚀
