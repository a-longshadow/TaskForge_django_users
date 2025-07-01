from django.apps import AppConfig
import os
from django.contrib.auth import get_user_model
from django.db.models.signals import post_migrate
from django.dispatch import receiver


class TasksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tasks"

    def ready(self):  # noqa: D401 – simple verb
        # Register a post_migrate hook that ensures a default super-user exists.
        @receiver(post_migrate)
        def _create_default_superuser(sender, **kwargs):  # noqa: ANN001 – signal kwargs
            User = get_user_model()

            username = os.getenv("DEFAULT_ADMIN_USER")
            password = os.getenv("DEFAULT_ADMIN_PASSWORD")
            email = os.getenv("DEFAULT_ADMIN_EMAIL", "")

            # Only create when credentials are supplied *and* user is absent.
            if username and password and not User.objects.filter(username=username).exists():
                User.objects.create_superuser(username=username, email=email, password=password) 