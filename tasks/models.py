from __future__ import annotations

import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.contrib.postgres.fields import JSONField  # Postgres backend extra
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password, check_password


class Meeting(models.Model):
    """Represents a source meeting coming from the n8n pipeline."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting_id = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=512)
    organizer_email = models.EmailField()
    date = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.title} ({self.date:%Y-%m-%d})"


class Task(models.Model):
    """Action items extracted from meetings and awaiting user review."""

    class Priority(models.TextChoices):
        HIGH = "High", "High"
        MEDIUM = "Medium", "Medium"
        LOW = "Low", "Low"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name="tasks")

    task_item = models.TextField()
    assignee_names = models.CharField(max_length=512, blank=True)
    assignee_emails = models.CharField(max_length=512, blank=True)
    priority = models.CharField(max_length=6, choices=Priority.choices, default=Priority.MEDIUM)
    brief_description = models.TextField()
    date_expected = models.DateField()

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    monday_item_id = models.CharField(max_length=255, blank=True, null=True)
    source_payload = models.JSONField(blank=True, null=True)
    auto_approved = models.BooleanField(default=False)
    posted_to_monday = models.BooleanField(default=False)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejected_reason = models.TextField(blank=True)
    expires_after_h = models.PositiveSmallIntegerField(default=24, help_text="Hours after creation during which the task is publicly visible for review.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.task_item[:50]}… ({self.get_status_display()})"


class ReviewAction(models.Model):
    """Audit trail of user approvals, rejections, or edits."""

    class Action(models.TextChoices):
        APPROVE = "approve", "Approve"
        REJECT = "reject", "Reject"
        EDIT = "edit", "Edit"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=7, choices=Action.choices)
    reason = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.get_action_display()} by {self.user or 'anonymous'} on {self.task_id}"


class PageLog(models.Model):
    """Simple per-request log for compliance & debugging."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    path = models.CharField(max_length=512)
    method = models.CharField(max_length=10)
    status_code = models.PositiveSmallIntegerField()
    remote_addr = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.method} {self.path} ({self.status_code})"


class AppSetting(models.Model):
    """Key→value table for runtime–editable settings (edited via Django admin).

    For security-sensitive values (API keys) ensure admin access is limited.
    """

    key = models.CharField(max_length=100, unique=True)
    value = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["key"]
        verbose_name = "App Setting"
        verbose_name_plural = "App Settings"

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.key}"

    @staticmethod
    def get(key: str, default: str | None = None) -> str | None:
        try:
            return AppSetting.objects.get(key=key).value
        except AppSetting.DoesNotExist:
            return default


class RawTranscript(models.Model):
    """Stores full Fireflies transcript JSON (can be very large)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file_name = models.CharField(max_length=255, unique=True)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name="transcripts", null=True, blank=True)
    data = models.JSONField()  # handles tens of thousands of lines
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Raw transcript"
        verbose_name_plural = "Raw transcripts"

    def __str__(self):
        return self.file_name


class ActionItem(Task):
    """Proxy model to expose Task under /admin/tasks/actionitem/."""

    class Meta:
        proxy = True
        verbose_name = "Task"
        verbose_name_plural = "Tasks"


class SecurityQuestion(models.Model):
    """Predefined security questions (3 rows seeded once)."""

    question_text = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name = "Security Question"
        verbose_name_plural = "Security Questions"

    def __str__(self) -> str:  # noqa: D401
        return self.question_text


class UserSecurityAnswer(models.Model):
    """Stores a user's answer (hashed) for a given security question."""

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    question = models.ForeignKey(SecurityQuestion, on_delete=models.CASCADE)
    answer_hash = models.CharField(max_length=128)

    class Meta:
        unique_together = ("user", "question")

    @classmethod
    def set_answer(cls, user, question, raw_answer: str):
        obj, _ = cls.objects.update_or_create(
            user=user,
            question=question,
            defaults={"answer_hash": make_password(raw_answer)},
        )
        return obj

    def check_answer(self, raw_answer: str) -> bool:  # noqa: D401
        return check_password(raw_answer, self.answer_hash) 