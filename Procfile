web: cd kyc_backend && gunicorn kyc_project.wsgi --log-file -
release: cd kyc_backend && python manage.py migrate && python manage.py seed_data
