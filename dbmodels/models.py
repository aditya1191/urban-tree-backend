from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

USER_ROLES = (
    ('admin', 'Administrator'),
    ('researcher', 'Researcher'),
    ('viewer', 'Viewer'),
)

class UserProfile(models.Model):
    """
    Extends the built-in User model to add roles and track login/logout times.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=USER_ROLES, default='viewer')
    last_login_time = models.DateTimeField(null=True, blank=True)
    last_logout_time = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.user.username
