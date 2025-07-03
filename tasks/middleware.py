from __future__ import annotations

import logging
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str
import json
import re

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


class PageLogMiddleware:
    """Middleware to log all page requests to the PageLog model."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process the request
        response = self.get_response(request)

        # Skip static files and admin media
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return response

        # Log the request
        try:
            PageLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                path=request.path[:500],  # Limit to 500 chars
                method=request.method,
                status_code=response.status_code,
                remote_addr=self.get_client_ip(request),
            )
        except Exception as e:
            logger.error(f"Failed to log page request: {e}")

        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AdminActionLogMiddleware:
    """Middleware to log all admin actions in detail."""

    def __init__(self, get_response):
        self.get_response = get_response
        # Compile regex patterns for admin URLs
        self.admin_url_pattern = re.compile(r'^/admin/')
        self.admin_change_pattern = re.compile(r'^/admin/\w+/\w+/(.+)/change/')
        self.admin_delete_pattern = re.compile(r'^/admin/\w+/\w+/(.+)/delete/')
        self.admin_add_pattern = re.compile(r'^/admin/\w+/\w+/add/')

    def __call__(self, request):
        # Store the original path for logging
        request.original_path = request.path
        
        # Process the request
        response = self.get_response(request)
        
        # Only log admin actions
        if not self.admin_url_pattern.match(request.path):
            return response
            
        # Skip admin media and static files
        if request.path.startswith('/admin/jsi18n/') or '/static/' in request.path:
            return response
            
        # Only log POST requests (actual actions)
        if request.method != 'POST':
            return response
            
        # Log the admin action
        try:
            self.log_admin_action(request, response)
        except Exception as e:
            logger.error(f"Failed to log admin action: {e}")
            
        return response
        
    def log_admin_action(self, request, response):
        """Log admin actions with detailed information."""
        if not request.user.is_authenticated or not request.user.is_staff:
            return
            
        path = request.original_path
        
        # Extract action type and details
        action_type = None
        object_id = None
        content_type = None
        action_details = {}
        
        # Try to determine the action type and object
        if self.admin_change_pattern.match(path):
            action_type = "Change"
            match = self.admin_change_pattern.match(path)
            if match:
                object_id = match.group(1)
                # Extract model name from path
                parts = path.split('/')
                if len(parts) > 3:
                    app_label = parts[2]
                    model_name = parts[3]
                    try:
                        content_type = ContentType.objects.get(app_label=app_label, model=model_name)
                    except ContentType.DoesNotExist:
                        pass
                        
        elif self.admin_delete_pattern.match(path):
            action_type = "Delete"
            match = self.admin_delete_pattern.match(path)
            if match:
                object_id = match.group(1)
                # Extract model name from path
                parts = path.split('/')
                if len(parts) > 3:
                    app_label = parts[2]
                    model_name = parts[3]
                    try:
                        content_type = ContentType.objects.get(app_label=app_label, model=model_name)
                    except ContentType.DoesNotExist:
                        pass
                        
        elif self.admin_add_pattern.match(path):
            action_type = "Add"
            # Extract model name from path
            parts = path.split('/')
            if len(parts) > 3:
                app_label = parts[2]
                model_name = parts[3]
                try:
                    content_type = ContentType.objects.get(app_label=app_label, model=model_name)
                except ContentType.DoesNotExist:
                    pass
        
        # Custom admin actions
        elif 'approve' in path.lower():
            action_type = "Approve"
            action_details["action"] = "approve"
        elif 'reject' in path.lower() or 'decline' in path.lower():
            action_type = "Reject"
            action_details["action"] = "reject"
        else:
            action_type = "Other Admin Action"
            
        # Extract POST data (excluding sensitive fields)
        post_data = {}
        for key, value in request.POST.items():
            if key not in ('csrfmiddlewaretoken', 'password', 'password1', 'password2'):
                post_data[key] = value if len(str(value)) < 100 else f"{str(value)[:100]}..."
                
        action_details["post_data"] = post_data
        action_details["path"] = path
        action_details["method"] = request.method
        action_details["status_code"] = response.status_code
        
        # Log to application logger
        logger.info(f"Admin action: {action_type} by {request.user.username} on {path}")
        
        # Create a LogEntry if we have enough information
        if content_type and action_type:
            action_flag = {
                "Add": ADDITION,
                "Change": CHANGE,
                "Delete": DELETION,
            }.get(action_type, CHANGE)  # Default to CHANGE for custom actions
            
            try:
                LogEntry.objects.log_action(
                    user_id=request.user.pk,
                    content_type_id=content_type.pk if content_type else None,
                    object_id=object_id if object_id else "",
                    object_repr=f"{content_type.model if content_type else 'Unknown'} {object_id if object_id else ''}",
                    action_flag=action_flag,
                    change_message=json.dumps(action_details),
                )
            except Exception as e:
                logger.error(f"Failed to create LogEntry: {e}") 