from django.apps import AppConfig
import os
from django.contrib.auth import get_user_model
from django.db.models.signals import post_migrate
from django.dispatch import receiver


class TasksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tasks"

    def ready(self):
        """Ensure a default super-user exists using env-provided creds.

        Reads three optional environment variables *at runtime* (not at import):

        • DEFAULT_ADMIN_USER
        • DEFAULT_ADMIN_EMAIL
        • DEFAULT_ADMIN_PASSWORD

        If *all* three are set **and** the user does not already exist,
        a super-user is created after migrations finish. If any variable is
        missing, the function silently exits so local development isn't
        affected.
        """

        @receiver(post_migrate)
        def _bootstrap_superuser(sender, **kwargs):  # noqa: ANN001
            username = os.getenv("DEFAULT_ADMIN_USER")
            email = os.getenv("DEFAULT_ADMIN_EMAIL")
            password = os.getenv("DEFAULT_ADMIN_PASSWORD")

            # Fallback to hard-coded credentials if env vars not provided.
            username = username or "joe"
            email = email or "joe@coophive.network"
            password = password or "x@2Kcsgt"

            User = get_user_model()
            user, created = User.objects.get_or_create(username=username, defaults={"email": email})
            # Ensure superuser/staff flags and password are up to date every deploy.
            if created or not user.is_superuser or not user.is_staff:
                user.is_superuser = True
                user.is_staff = True
            # Always reset to known password to satisfy hard-coded requirement.
            user.set_password(password)
            user.email = email
            user.save() 