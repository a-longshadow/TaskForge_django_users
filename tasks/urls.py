from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MeetingViewSet, TaskViewSet, IngestView

app_name = "tasks"

router = DefaultRouter()
router.register(r"meetings", MeetingViewSet, basename="meeting")
router.register(r"tasks", TaskViewSet, basename="task")

urlpatterns = [
    path("ingest/", IngestView.as_view(), name="ingest"),
    path("", include(router.urls)),
] 