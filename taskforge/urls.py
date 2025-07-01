from django.contrib import admin
from django.urls import include, path
from django.http import JsonResponse
from django.views.generic import RedirectView
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from tasks.health import health_view
from tasks.views import HomeView, PublicActionItemView

urlpatterns = [
    path("health/", health_view, name="health"),
    path("admin/", admin.site.urls),
    path("api/", include("tasks.urls", namespace="tasks")),
    # Public page for approved items
    path("user-approved/", include("tasks.public_urls", namespace="public")),
    path("", HomeView.as_view(), name="home"),
    path("tasks/", PublicActionItemView.as_view(), name="public-tasks"),
    path("", RedirectView.as_view(url="/admin/", permanent=False)),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()

from django.conf.urls import handler404
handler404 = "taskforge.views.custom_404" 