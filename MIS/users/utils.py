# utils.py - CREATE THIS FILE
from django.utils import timezone
from .models import UserActivity  # Adjust app name

def log_activity(user, action, details=""):
    UserActivity.objects.create(
        user=user,
        action=action,
        details=details
    )