from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ApprovedPublicViewSet

app_name = "public"

router = DefaultRouter()
router.register(r"", ApprovedPublicViewSet, basename="approved")

urlpatterns = [
    path("", include(router.urls)),
] 