from rest_framework import serializers

from .models import Meeting, Task, ReviewAction


class MeetingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meeting
        fields = [
            "id",
            "meeting_id",
            "title",
            "organizer_email",
            "date",
        ]


class TaskSerializer(serializers.ModelSerializer):
    meeting = MeetingSerializer(read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "meeting",
            "task_item",
            "assignee_names",
            "assignee_emails",
            "priority",
            "brief_description",
            "date_expected",
            "status",
            "monday_item_id",
            "posted_to_monday",
            "reviewed_at",
            "rejected_reason",
            "expires_after_h",
            "source_payload",
            "created_at",
            "updated_at",
            "auto_approved",
        ]
        read_only_fields = [
            "status",
            "monday_item_id",
            "reviewed_at",
            "created_at",
            "updated_at",
        ]


class TaskActionSerializer(serializers.Serializer):
    """Approve / reject / edit serializer.

    Edits are limited to appending to brief_description and/or changing date_expected.
    """

    ACTION_CHOICES = (
        ("approve", "Approve"),
        ("reject", "Reject"),
    )

    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    reason = serializers.CharField(required=False, allow_blank=True)
    new_brief_description = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    new_date_expected = serializers.DateField(required=False)

    def validate(self, attrs):
        action = attrs.get("action")
        if action == "reject" and not attrs.get("reason"):
            raise serializers.ValidationError("A reason is required when rejecting a task.")
        if action == "reject":
            words = attrs.get("reason", "").strip().split()
            if len(words) < 5:
                raise serializers.ValidationError("Rejection reason must be at least 5 words.")
        return attrs


class ReviewActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewAction
        fields = [
            "id",
            "task",
            "user",
            "action",
            "reason",
            "timestamp",
        ] 