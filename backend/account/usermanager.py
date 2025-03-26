from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        # Print the received data
        print("Creating user with:", email, extra_fields)

        if not email:
            raise ValueError(_("Email is required"))
        if not extra_fields.get("first_name"):
            print("first_name missing from:", extra_fields)  # Debug print
            raise ValueError(_("First name is required"))
        if not extra_fields.get("last_name"):
            raise ValueError(_("Last name is required"))
        if password and len(password) < 8:
            raise ValueError(_("Password must be at least 8 characters"))

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(email=email, password=password, **extra_fields)
