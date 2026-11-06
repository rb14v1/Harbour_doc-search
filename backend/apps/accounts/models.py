from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.accounts.managers import UserManager


class User(AbstractUser):
    """Single-role user. The documents app scopes every queryset to
    request.user - there is no admin/manager distinction in this demo app
    beyond Django's own is_staff/is_superuser for the admin site."""

    username = None
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email
