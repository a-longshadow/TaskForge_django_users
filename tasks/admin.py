from django.contrib import admin

from .models import Meeting, Task, ReviewAction, PageLog, AppSetting, RawTranscript, ActionItem, SecurityQuestion, UserSecurityAnswer


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ("title", "organizer_email", "date", "meeting_id")
    search_fields = ("title", "organizer_email", "meeting_id")


class BaseTaskAdmin(admin.ModelAdmin):
    list_display = (
        "task_item",
        "meeting",
        "priority",
        "status",
        "date_expected",
    )
    list_filter = ("priority", "status")
    search_fields = ("task_item", "assignee_names", "assignee_emails")


# unregister Task if previously registered
try:
    admin.site.unregister(Task)
except admin.sites.NotRegistered:
    pass


@admin.register(ActionItem)
class ActionItemAdmin(BaseTaskAdmin):
    pass


@admin.register(ReviewAction)
class ReviewActionAdmin(admin.ModelAdmin):
    list_display = ("task", "user", "action", "timestamp")
    list_filter = ("action",)


@admin.register(PageLog)
class PageLogAdmin(admin.ModelAdmin):
    list_display = (
        "path",
        "method",
        "status_code",
        "remote_addr",
        "timestamp",
    )
    list_filter = ("method", "status_code")
    search_fields = ("user__username", "path", "remote_addr")


@admin.register(AppSetting)
class AppSettingAdmin(admin.ModelAdmin):
    list_display = ("key", "updated_at")
    search_fields = ("key",)


@admin.register(RawTranscript)
class RawTranscriptAdmin(admin.ModelAdmin):
    list_display = ("file_name", "meeting", "created_at")
    search_fields = ("file_name", "meeting__title")


@admin.register(SecurityQuestion)
class SecurityQuestionAdmin(admin.ModelAdmin):
    list_display = ("question_text",)


@admin.register(UserSecurityAnswer)
class UserSecurityAnswerAdmin(admin.ModelAdmin):
    list_display = ("user", "question")


try:
    admin.site.unregister(Meeting)
except admin.sites.NotRegistered:
    pass 