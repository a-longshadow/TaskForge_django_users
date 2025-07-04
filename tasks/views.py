from __future__ import annotations

import time
import logging
from datetime import datetime

from django.db import transaction
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.views.generic import TemplateView, ListView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

from .models import Meeting, Task, ReviewAction, SecurityQuestion, UserSecurityAnswer
from .serializers import (
    MeetingSerializer,
    TaskSerializer,
    TaskActionSerializer,
    ReviewActionSerializer,
)
from .services import create_monday_item

logger = logging.getLogger(__name__)


class MeetingViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """Read-only API for meeting metadata."""

    queryset = Meeting.objects.all()
    serializer_class = MeetingSerializer
    permission_classes = [IsAuthenticated]


class TaskViewSet(viewsets.ModelViewSet):
    """CRUD + approve/reject for tasks (publicly accessible)."""

    queryset = Task.objects.select_related("meeting").order_by("-meeting__date", "-created_at")
    serializer_class = TaskSerializer
    permission_classes = [AllowAny]
    authentication_classes = []  # Disable SessionAuthentication to avoid CSRF for public calls

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        return qs

    @action(methods=["post"], detail=True, url_path="act")
    def act(self, request, pk=None):  # type: ignore[override]
        """Approve, reject, or edit a task with 5-second confirmation window."""

        task: Task = self.get_object()
        serializer = TaskActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # 5-second wait/confirm (client should call again with confirm=true) – backend side just logs
        confirm = request.query_params.get("confirm") == "true"
        if not confirm:
            logger.debug("Preview requested before confirmation for task %s", task.id)
            return Response(
                {
                    "message": "Preview. Resend the same request with ?confirm=true within 5 seconds to apply.",
                    "payload": data,
                },
                status=status.HTTP_202_ACCEPTED,
            )

        # Optional sleep to allow front-end confirmation countdown (defensive)
        time.sleep(1)  # noqa: S311 – brief delay, not blocking worker significantly

        with transaction.atomic():
            action = data["action"]
            reason = data.get("reason", "")

            # Handle brief_description append and date change
            new_desc = data.get("new_brief_description") or data.get("description")
            if new_desc:
                task.brief_description += f"\n\n[Edit] {new_desc}"

            if date := data.get("new_date_expected"):
                task.date_expected = date

            if action == "approve":
                task.status = Task.Status.APPROVED
                task.reviewed_at = timezone.now()
            else:
                task.status = Task.Status.REJECTED
                task.reviewed_at = timezone.now()
                task.rejected_reason = reason

            task.save()

            # Log action
            ReviewAction.objects.create(
                task=task,
                user=request.user if request.user.is_authenticated else None,
                action=ReviewAction.Action.APPROVE if action == "approve" else ReviewAction.Action.REJECT,
                reason=reason,
            )

        # On approval, push to Monday.com if not already pushed
        if task.status == Task.Status.APPROVED and not task.monday_item_id:
            item_id = create_monday_item(task)
            if item_id:
                task.monday_item_id = item_id
                task.posted_to_monday = True
                task.save(update_fields=["monday_item_id", "posted_to_monday"])
                logger.info(f"Task {task.id} successfully sent to Monday.com with item_id={item_id}")
            else:
                logger.error(f"Failed to send task {task.id} to Monday.com")

        return Response(TaskSerializer(task, context={"request": request}).data)

    @action(methods=["post"], detail=True, url_path="approve")
    def approve(self, request, pk=None):
        """Approve a task and send to Monday.com."""
        task = self.get_object()
        
        # Confirm parameter required
        confirm = request.query_params.get("confirm") == "true"
        if not confirm:
            return Response(
                {
                    "message": "Preview. Resend with ?confirm=true to apply.",
                },
                status=status.HTTP_202_ACCEPTED,
            )
            
        # Process the approval
        with transaction.atomic():
            task.status = Task.Status.APPROVED
            task.reviewed_at = timezone.now()
            task.save()
            
            # Log action
            ReviewAction.objects.create(
                task=task,
                user=request.user if request.user.is_authenticated else None,
                action=ReviewAction.Action.APPROVE,
            )
            
        # Send to Monday.com
        if not task.monday_item_id:
            item_id = create_monday_item(task)
            if item_id:
                task.monday_item_id = item_id
                task.posted_to_monday = True
                task.save(update_fields=["monday_item_id", "posted_to_monday"])
                logger.info(f"Task {task.id} successfully sent to Monday.com with item_id={item_id}")
            else:
                logger.error(f"Failed to send task {task.id} to Monday.com")
            
        return Response(TaskSerializer(task, context={"request": request}).data)

    @action(methods=["post"], detail=True, url_path="reject")
    def reject(self, request, pk=None):
        """Reject a task with a reason."""
        task = self.get_object()
        
        # Validate the reason
        reason = request.data.get("reason", "").strip()
        if not reason:
            return Response(
                {"detail": "A reason is required when rejecting a task."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        words = reason.split()
        if len(words) < 5:
            return Response(
                {"detail": "Rejection reason must be at least 5 words."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Confirm parameter required
        confirm = request.query_params.get("confirm") == "true"
        if not confirm:
            return Response(
                {
                    "message": "Preview. Resend with ?confirm=true to apply.",
                    "reason": reason,
                },
                status=status.HTTP_202_ACCEPTED,
            )
            
        # Process the rejection
        with transaction.atomic():
            task.status = Task.Status.REJECTED
            task.reviewed_at = timezone.now()
            task.rejected_reason = reason
            task.save()
            
            # Log action
            ReviewAction.objects.create(
                task=task,
                user=request.user if request.user.is_authenticated else None,
                action=ReviewAction.Action.REJECT,
                reason=reason,
            )
            
        return Response(TaskSerializer(task, context={"request": request}).data)

    @action(methods=["patch"], detail=True, url_path="edit")
    def edit(self, request, pk=None):
        return self._handle_edit(request, pk)

    def _handle_simple_action(self, request, pk, action: str):
        task = self.get_object()
        serializer = TaskActionSerializer(data={"action": action, **request.data})
        serializer.is_valid(raise_exception=True)
        # proxy to act() behaviour via duplication to avoid code duplication? for brevity use existing act method logic
        request._full_data = serializer.validated_data  # type: ignore
        return self.act(request, pk)

    def _handle_edit(self, request, pk):
        task = self.get_object()
        serializer = TaskActionSerializer(data={"action": "approve", **request.data})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        new_desc = data.get("new_brief_description") or data.get("description")
        if new_desc:
            task.brief_description = new_desc
        if date := data.get("new_date_expected"):
            task.date_expected = date
        task.save()
        return Response(TaskSerializer(task, context={"request": request}).data)


class ApprovedPublicViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Public-facing read-only endpoint for approved tasks (no auth)."""

    queryset = Task.objects.filter(status=Task.Status.APPROVED).select_related("meeting").order_by("-meeting__date", "-created_at")
    serializer_class = TaskSerializer
    permission_classes = [AllowAny]


class IngestView(APIView):
    """Endpoint that n8n HTTP Request node POSTs to.

    Expects the same structure produced by "Build payload · GDrive & Monday.com" node,
    specifically the `monday_tasks` array plus meeting/context metadata.
    """

    permission_classes = [AllowAny]  # n8n can hit without auth; secure via token in env maybe

    def post(self, request, *args, **kwargs):  # noqa: D401
        payload = request.data
        tasks_data = payload.get("monday_tasks", [])
        if not tasks_data:
            return Response({"detail": "monday_tasks missing or empty"}, status=400)

        # Get meeting IDs from the payload
        meeting_ids = {t.get("meeting_id") for t in tasks_data if t.get("meeting_id")}
        if not meeting_ids:
            logger.warning("No meeting IDs found in payload")
            return Response({"detail": "no_meeting_ids"}, status=400)
            
        created = 0
        updated = 0
        
        for t in tasks_data:
            meeting_id = t.get("meeting_id")
            if not meeting_id:
                continue
                
            # Get or create the meeting
            meeting_date = timezone.now()
            if 'meeting_date' in payload:
                try:
                    # Convert from milliseconds timestamp to datetime
                    if isinstance(payload['meeting_date'], str) and payload['meeting_date'].isdigit():
                        meeting_date = datetime.fromtimestamp(int(payload['meeting_date']) / 1000, tz=timezone.utc)
                    elif isinstance(payload['meeting_date'], int):
                        meeting_date = datetime.fromtimestamp(payload['meeting_date'] / 1000, tz=timezone.utc)
                except (ValueError, TypeError):
                    pass
            
            # Parse generated_at if available
            generated_at = None
            if 'generated_at' in payload:
                try:
                    generated_at = datetime.fromisoformat(payload['generated_at'].replace('Z', '+00:00'))
                except (ValueError, TypeError, AttributeError):
                    pass

            meeting_obj, _ = Meeting.objects.get_or_create(
                meeting_id=meeting_id,
                defaults={
                    "title": t.get("meeting_title", "Untitled"),
                    "organizer_email": t.get("meeting_organizer", "unknown@example.com"),
                    "date": meeting_date,
                    "execution_id": payload.get("execution_id"),
                    "generated_at": generated_at,
                },
            )
            
            # Update meeting with execution_id and generated_at if they weren't set before
            if (payload.get("execution_id") and not meeting_obj.execution_id) or \
               (generated_at and not meeting_obj.generated_at):
                meeting_obj.execution_id = payload.get("execution_id", meeting_obj.execution_id)
                if generated_at:
                    meeting_obj.generated_at = generated_at
                meeting_obj.save(update_fields=['execution_id', 'generated_at'])
            
            # Try to find an existing task
            task_item = t.get("task_item")
            existing_task = Task.objects.filter(
                meeting=meeting_obj, 
                task_item=task_item
            ).first()
            
            if existing_task:
                # Update the existing task with new data
                existing_task.assignee_names = t.get("assignee(s)_full_names", existing_task.assignee_names)
                existing_task.assignee_emails = t.get("assignee_emails", existing_task.assignee_emails)
                existing_task.priority = t.get("priority", existing_task.priority)
                existing_task.brief_description = t.get("brief_description", existing_task.brief_description)
                
                # Handle date_expected parsing
                if t.get("date_expected"):
                    try:
                        # Try standard ISO format
                        date_expected = datetime.strptime(t.get("date_expected"), '%Y-%m-%d').date()
                        existing_task.date_expected = date_expected
                    except ValueError:
                        try:
                            # Try human-readable format
                            date_expected = datetime.strptime(t.get("date_expected"), '%B %d, %Y').date()
                            existing_task.date_expected = date_expected
                        except ValueError:
                            # Keep existing date if parsing fails
                            pass
                
                existing_task.source_payload = t
                
                # Only update auto_approved if it's explicitly set in the payload
                if t.get("approved") is not None:
                    existing_task.auto_approved = t.get("approved")
                    
                existing_task.save()
                updated += 1
                logger.info(f"Updated task: {task_item[:50]}...")
            else:
                # Create a new task
                date_expected = timezone.now().date()
                if t.get("date_expected"):
                    try:
                        # Try standard ISO format
                        date_expected = datetime.strptime(t.get("date_expected"), '%Y-%m-%d').date()
                    except ValueError:
                        try:
                            # Try human-readable format
                            date_expected = datetime.strptime(t.get("date_expected"), '%B %d, %Y').date()
                        except ValueError:
                            # Keep default if parsing fails
                            pass
                
                task_obj = Task.objects.create(
                    meeting=meeting_obj,
                    task_item=task_item,
                    assignee_names=t.get("assignee(s)_full_names", ""),
                    assignee_emails=t.get("assignee_emails", ""),
                    priority=t.get("priority", Task.Priority.MEDIUM),
                    brief_description=t.get("brief_description", ""),
                    date_expected=date_expected,
                    source_payload=t,
                    auto_approved=t.get("approved", False)
                )
                created += 1
                logger.info(f"Created task: {task_item[:50]}...")

        return Response({"created": created, "updated": updated})


class HomeView(TemplateView):
    template_name = "home.html"


class PublicActionItemView(ListView):
    """Public list of tasks pending review, grouped by meeting."""

    template_name = "public_tasks.html"
    context_object_name = "tasks"

    def get_queryset(self):
        from datetime import timedelta

        cutoff = timezone.now() - timedelta(hours=24)
        # Show all tasks, including those that have been reviewed
        return Task.objects.select_related("meeting").order_by("-meeting__date", "-created_at")


@csrf_exempt
def reset_password_via_questions(request):
    """POST JSON: {"username":"joe","answers":[{"id":1,"answer":"foo"}, ...],"new_password":"bar"}"""
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    try:
        data = json.loads(request.body.decode())
        username = data["username"]
        new_password = data["new_password"]
        answers = data["answers"]  # list of {id, answer}
    except (KeyError, ValueError):
        return JsonResponse({"detail": "Invalid payload"}, status=400)

    User = get_user_model()
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({"detail": "Invalid user"}, status=404)

    # Verify answers (must supply at least two correct of three)
    correct = 0
    for item in answers:
        try:
            q = SecurityQuestion.objects.get(id=item["id"])
            ans_obj = UserSecurityAnswer.objects.get(user=user, question=q)
            if ans_obj.check_answer(item["answer"]):
                correct += 1
        except (SecurityQuestion.DoesNotExist, UserSecurityAnswer.DoesNotExist):
            continue

    if correct < 2:
        return JsonResponse({"detail": "Security answers incorrect"}, status=403)

    user.set_password(new_password)
    user.save()
    return JsonResponse({"detail": "Password reset successful"}) 