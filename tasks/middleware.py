from __future__ import annotations

import logging
from django.utils.deprecation import MiddlewareMixin

from .models import PageLog

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """Persist a minimal audit trail for each HTTP request."""

    def process_response(self, request, response):  # type: ignore[override]
        try:
            PageLog.objects.create(
                user=request.user if hasattr(request, "user") and request.user.is_authenticated else None,
                path=request.path,
                method=request.method,
                status_code=response.status_code,
                remote_addr=request.META.get("REMOTE_ADDR"),
            )
        except Exception as exc:  # pragma: no cover – never fail the request
            logger.debug("Could not write PageLog: %s", exc, exc_info=True)
        return response 