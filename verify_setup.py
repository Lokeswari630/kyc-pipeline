#!/usr/bin/env python3
"""
Setup Validation Script for KYC Application

Run this after initial setup to verify everything is correct:
  python verify_setup.py
"""

import os
import sys
from pathlib import Path

def check_file_exists(path, description=""):
    """Check if a file exists and is readable."""
    exists = os.path.exists(path)
    status = "✅" if exists else "❌"
    desc = f" ({description})" if description else ""
    print(f"  {status} {path}{desc}")
    return exists

def check_python_packages():
    """Check if required Python packages are installed."""
    print("\n📦 Checking Python Packages...")
    required = {
        'django': 'Django',
        'rest_framework': 'DRF',
        'corsheaders': 'CORS',
    }
    
    all_ok = True
    for package, name in required.items():
        try:
            __import__(package)
            print(f"  ✅ {name}")
        except ImportError:
            print(f"  ❌ {name} - NOT INSTALLED")
            all_ok = False
    
    return all_ok

def check_node_packages():
    """Check if node_modules exists."""
    print("\n📦 Checking Node Packages...")
    npm_path = Path("kyc_frontend/node_modules")
    if npm_path.exists():
        print(f"  ✅ node_modules found")
        return True
    else:
        print(f"  ❌ node_modules NOT found - Run: npm install")
        return False

def check_backend_structure():
    """Check backend file structure."""
    print("\n📁 Backend Structure...")
    
    files = [
        ("kyc_backend/manage.py", "Django management"),
        ("kyc_backend/requirements.txt", "Dependencies"),
        ("kyc_backend/seed.py", "Seed data"),
        ("kyc_backend/kyc_project/settings.py", "Django settings"),
        ("kyc_backend/kyc_app/models.py", "Models"),
        ("kyc_backend/kyc_app/views.py", "Views"),
        ("kyc_backend/kyc_app/state_machine.py", "State machine"),
        ("kyc_backend/kyc_app/file_validator.py", "File validation"),
        ("kyc_backend/kyc_app/permissions.py", "Permissions"),
        ("kyc_backend/kyc_app/tests.py", "Tests"),
        ("kyc_backend/README.md", "README"),
        ("kyc_backend/EXPLAINER.md", "Explainer"),
        ("kyc_backend/QUICKSTART.md", "Quick start"),
    ]
    
    all_ok = True
    for path, desc in files:
        if not check_file_exists(path, desc):
            all_ok = False
    
    return all_ok

def check_frontend_structure():
    """Check frontend file structure."""
    print("\n📁 Frontend Structure...")
    
    files = [
        ("kyc_frontend/package.json", "Dependencies"),
        ("kyc_frontend/vite.config.js", "Vite config"),
        ("kyc_frontend/tailwind.config.js", "Tailwind config"),
        ("kyc_frontend/index.html", "HTML entry"),
        ("kyc_frontend/src/main.jsx", "React entry"),
        ("kyc_frontend/src/App.jsx", "App component"),
        ("kyc_frontend/src/api.js", "API setup"),
        ("kyc_frontend/src/context/AuthContext.jsx", "Auth context"),
        ("kyc_frontend/src/pages/Login.jsx", "Login page"),
        ("kyc_frontend/src/pages/MerchantDashboard.jsx", "Merchant dashboard"),
        ("kyc_frontend/src/pages/MerchantForm.jsx", "Merchant form"),
        ("kyc_frontend/src/pages/ReviewerDashboard.jsx", "Reviewer dashboard"),
        ("kyc_frontend/src/components/ProtectedRoute.jsx", "Protected routes"),
    ]
    
    all_ok = True
    for path, desc in files:
        if not check_file_exists(path, desc):
            all_ok = False
    
    return all_ok

def check_database():
    """Check if database is created."""
    print("\n🗄️  Database...")
    db_path = Path("kyc_backend/db.sqlite3")
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        print(f"  ✅ db.sqlite3 exists ({size_mb:.2f} MB)")
        return True
    else:
        print(f"  ❌ db.sqlite3 NOT found - Run: python manage.py migrate")
        return False

def print_next_steps(issues):
    """Print next steps based on issues found."""
    print("\n" + "="*50)
    print("📋 NEXT STEPS")
    print("="*50)
    
    if issues['python_packages']:
        print("\n1. Install Python packages:")
        print("   cd kyc_backend")
        print("   pip install -r requirements.txt")
    
    if issues['database']:
        print("\n2. Create database:")
        print("   python manage.py migrate")
        print("   python manage.py shell < seed.py")
    
    if issues['node_packages']:
        print("\n3. Install Node packages:")
        print("   cd kyc_frontend")
        print("   npm install")
    
    if not any(issues.values()):
        print("\n✅ All checks passed! Ready to start.")
        print("\nStart backend (Terminal 1):")
        print("  cd kyc_backend")
        print("  python manage.py runserver")
        print("\nStart frontend (Terminal 2):")
        print("  cd kyc_frontend")
        print("  npm run dev")
        print("\nAccess application:")
        print("  Frontend: http://localhost:3000/login")
        print("  Admin: http://localhost:8000/admin")

def main():
    """Run all checks."""
    print("="*50)
    print("KYC APPLICATION - SETUP VERIFICATION")
    print("="*50)
    
    os.chdir(Path(__file__).parent)
    
    issues = {
        'python_packages': False,
        'node_packages': False,
        'backend_files': False,
        'frontend_files': False,
        'database': False,
    }
    
    # Run checks
    if not check_python_packages():
        issues['python_packages'] = True
    
    if not check_node_packages():
        issues['node_packages'] = True
    
    if not check_backend_structure():
        issues['backend_files'] = True
    
    if not check_frontend_structure():
        issues['frontend_files'] = True
    
    if not check_database():
        issues['database'] = True
    
    # Print summary
    print("\n" + "="*50)
    print("✅ SUMMARY")
    print("="*50)
    
    total_issues = sum(issues.values())
    
    if total_issues == 0:
        print("✅ All checks passed! No issues found.")
    else:
        print(f"⚠️  {total_issues} issue(s) found. See above for details.")
    
    print("\n" + "="*50)
    
    # Print next steps
    print_next_steps(issues)
    
    print("\n" + "="*50)
    
    return 0 if total_issues == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
