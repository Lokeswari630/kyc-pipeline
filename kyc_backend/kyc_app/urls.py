"""
URL routing for KYC app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'kyc', views.KYCSubmissionViewSet, basename='kyc-submission')
router.register(r'auth', views.AuthViewSet, basename='auth')
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'notifications', views.NotificationViewSet, basename='notification')

urlpatterns = [
    path('', views.api_root, name='api-root'),
    path('', include(router.urls)),
]
