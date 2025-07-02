from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from django.template.response import TemplateResponse
from django.http import HttpResponseRedirect

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
    list_display = BaseTaskAdmin.list_display + ("status", "reviewed_at", "posted_to_monday", "admin_actions")
    list_filter = ("status", "priority", "posted_to_monday")
    readonly_fields = ('action_buttons',)
    
    fieldsets = (
        (None, {
            'fields': ('meeting', 'task_item', 'assignee_names', 'assignee_emails', 'priority', 
                      'brief_description', 'date_expected')
        }),
        ('Review Status', {
            'fields': ('status', 'reviewed_at', 'rejected_reason', 'action_buttons')
        }),
        ('Monday.com', {
            'fields': ('monday_item_id', 'posted_to_monday')
        }),
        ('Advanced', {
            'classes': ('collapse',),
            'fields': ('auto_approved', 'expires_after_h', 'source_payload')
        }),
    )

    actions = ["approve_send_to_monday", "decline_tasks"]
    
    def admin_actions(self, obj):
        """Add action buttons to the list view."""
        if obj.status == Task.Status.PENDING:
            approve_url = reverse('admin:approve_task', args=[obj.pk])
            reject_url = reverse('admin:reject_task', args=[obj.pk])
            
            return format_html(
                '<a class="button" href="{}" style="background-color: #10B981; color: white; padding: 3px 8px; border-radius: 4px; text-decoration: none; margin-right: 5px;">Approve</a>'
                '<a class="button" href="{}" style="background-color: #EF4444; color: white; padding: 3px 8px; border-radius: 4px; text-decoration: none;">Decline</a>',
                approve_url, reject_url
            )
        elif obj.status == Task.Status.APPROVED:
            return format_html(
                '<span style="background-color: #10B981; color: white; padding: 3px 8px; border-radius: 4px; opacity: 0.7;">Approved</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #6B7280; color: white; padding: 3px 8px; border-radius: 4px; opacity: 0.7;">Declined</span>'
            )
    
    admin_actions.short_description = "Actions"

    def action_buttons(self, obj):
        """Custom field to display action buttons in the admin form."""
        if obj.status == Task.Status.PENDING:
            approve_url = reverse('admin:approve_task', args=[obj.pk])
            reject_url = reverse('admin:reject_task', args=[obj.pk])
            
            return format_html(
                '<div class="submit-row" style="margin-top: 10px;">'
                '<a href="{}" class="button default" style="background-color: #10B981; color: white; margin-right: 8px;" '
                'onclick="return confirm(\'Are you sure you want to approve this task and send it to Monday.com?\')">Approve & Send to Monday</a>'
                '<a href="{}" class="button" style="background-color: #EF4444; color: white;" '
                'onclick="return confirm(\'Are you sure you want to decline this task?\')">Decline Task</a>'
                '</div>',
                approve_url, reject_url
            )
        else:
            status_class = "success" if obj.status == Task.Status.APPROVED else "error"
            status_text = obj.get_status_display()
            
            return format_html(
                '<div class="submit-row" style="margin-top: 10px;">'
                '<span class="button {}" style="opacity: 0.7; cursor: default;">Task is {}</span>'
                '</div>',
                status_class, status_text
            )
    
    action_buttons.short_description = "Actions"

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<uuid:task_id>/approve/',
                self.admin_site.admin_view(self.approve_task_view),
                name='approve_task',
            ),
            path(
                '<uuid:task_id>/reject/',
                self.admin_site.admin_view(self.reject_task_view),
                name='reject_task',
            ),
            path(
                'bulk-approve/',
                self.admin_site.admin_view(self.bulk_approve_view),
                name='bulk_approve',
            ),
            path(
                'bulk-reject/',
                self.admin_site.admin_view(self.bulk_reject_view),
                name='bulk_reject',
            ),
        ]
        return custom_urls + urls
    
    def approve_task_view(self, request, task_id):
        """View to approve a single task and send to Monday.com."""
        from .services import create_monday_item
        
        try:
            task = ActionItem.objects.get(pk=task_id, status=Task.Status.PENDING)
            
            # Check if confirmation is needed
            if 'confirm' not in request.POST:
                context = {
                    'title': "Confirm approval",
                    'task': task,
                    'action': 'approve',
                    'opts': self.model._meta,
                    'app_label': self.model._meta.app_label,
                }
                return TemplateResponse(request, 'admin/tasks/confirm_action.html', context)
            
            # Try to create Monday item
            item_id = create_monday_item(task)
            if item_id:
                task.status = Task.Status.APPROVED
                task.reviewed_at = timezone.now()
                task.monday_item_id = item_id
                task.posted_to_monday = True
                task.save()
                
                # Log the action
                ReviewAction.objects.create(
                    task=task,
                    user=request.user,
                    action=ReviewAction.Action.APPROVE
                )
                
                messages.success(request, f"Task '{task.task_item}' approved and sent to Monday.com successfully.")
            else:
                messages.error(request, f"Failed to send task '{task.task_item}' to Monday.com. Check logs for details.")
                
        except ActionItem.DoesNotExist:
            messages.error(request, "Task not found or already processed.")
        
        # Redirect back to the change page
        return redirect(reverse('admin:tasks_actionitem_change', args=[task_id]))
    
    def reject_task_view(self, request, task_id):
        """View to reject a single task."""
        try:
            task = ActionItem.objects.get(pk=task_id, status=Task.Status.PENDING)
            
            # Check if confirmation is needed
            if 'confirm' not in request.POST:
                context = {
                    'title': "Confirm rejection",
                    'task': task,
                    'action': 'reject',
                    'opts': self.model._meta,
                    'app_label': self.model._meta.app_label,
                }
                return TemplateResponse(request, 'admin/tasks/confirm_action.html', context)
            
            # Process the rejection
            task.status = Task.Status.REJECTED
            task.reviewed_at = timezone.now()
            task.rejected_reason = request.POST.get('rejected_reason', "Declined by admin")
            task.save()
            
            # Log the action
            ReviewAction.objects.create(
                task=task,
                user=request.user,
                action=ReviewAction.Action.REJECT,
                reason=task.rejected_reason
            )
            
            messages.success(request, f"Task '{task.task_item}' declined successfully.")
        except ActionItem.DoesNotExist:
            messages.error(request, "Task not found or already processed.")
        
        # Redirect back to the change page
        return redirect(reverse('admin:tasks_actionitem_change', args=[task_id]))

    @admin.action(description="Approve & send to Monday")
    def approve_send_to_monday(self, request, queryset):
        """Bulk action to approve tasks and send to Monday.com."""
        selected = request.POST.getlist("_selected_action")
        
        # Filter only pending tasks
        pending_tasks = queryset.filter(status=Task.Status.PENDING)
        if not pending_tasks:
            messages.warning(request, "No pending tasks selected for approval.")
            return
            
        context = {
            'title': "Confirm bulk approval",
            'tasks': pending_tasks,
            'action': 'approve',
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
        }
        return TemplateResponse(request, 'admin/tasks/confirm_bulk_action.html', context)

    @admin.action(description="Decline selected tasks")
    def decline_tasks(self, request, queryset):
        """Bulk action to decline tasks."""
        selected = request.POST.getlist("_selected_action")
        
        # Filter only pending tasks
        pending_tasks = queryset.filter(status=Task.Status.PENDING)
        if not pending_tasks:
            messages.warning(request, "No pending tasks selected for rejection.")
            return
            
        context = {
            'title': "Confirm bulk rejection",
            'tasks': pending_tasks,
            'action': 'reject',
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
        }
        return TemplateResponse(request, 'admin/tasks/confirm_bulk_action.html', context)
        
    def bulk_approve_view(self, request):
        """View to handle bulk approve confirmation."""
        selected = request.POST.getlist('_selected_action')
        if not selected:
            messages.error(request, "No tasks selected for approval.")
            return redirect('admin:tasks_actionitem_changelist')
            
        tasks = ActionItem.objects.filter(pk__in=selected, status=Task.Status.PENDING)
        if 'confirm' in request.POST:
            return self.process_bulk_approve(request, tasks)
        
        context = {
            'title': "Confirm bulk approval",
            'tasks': tasks,
            'action': 'approve',
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
        }
        return TemplateResponse(request, 'admin/tasks/confirm_bulk_action.html', context)
        
    def process_bulk_approve(self, request, queryset):
        """Process the bulk approval after confirmation."""
        from .services import create_monday_item
        
        success_count = 0
        error_count = 0

        for task in queryset:
            item_id = create_monday_item(task)
            if item_id:
                task.status = Task.Status.APPROVED
                task.reviewed_at = timezone.now()
                task.monday_item_id = item_id
                task.posted_to_monday = True
                task.save()
                
                # Log the action
                ReviewAction.objects.create(
                    task=task,
                    user=request.user,
                    action=ReviewAction.Action.APPROVE
                )
                
                success_count += 1
            else:
                error_count += 1
        
        if success_count:
            messages.success(request, f"{success_count} task(s) approved and sent to Monday.com successfully.")
        if error_count:
            messages.error(request, f"Failed to send {error_count} task(s) to Monday.com. Check logs for details.")
            
        return redirect('admin:tasks_actionitem_changelist')
    
    def bulk_reject_view(self, request):
        """View to handle bulk reject confirmation."""
        selected = request.POST.getlist('_selected_action')
        if not selected:
            messages.error(request, "No tasks selected for rejection.")
            return redirect('admin:tasks_actionitem_changelist')
            
        tasks = ActionItem.objects.filter(pk__in=selected, status=Task.Status.PENDING)
        if 'confirm' in request.POST:
            return self.process_bulk_reject(request, tasks)
        
        context = {
            'title': "Confirm bulk rejection",
            'tasks': tasks,
            'action': 'reject',
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
        }
        return TemplateResponse(request, 'admin/tasks/confirm_bulk_action.html', context)
    
    def process_bulk_reject(self, request, queryset):
        """Process the bulk rejection after confirmation."""
        count = 0
        for task in queryset:
            task.status = Task.Status.REJECTED
            task.reviewed_at = timezone.now()
            task.rejected_reason = "Declined by admin"
            task.save()
            
            # Log the action
            ReviewAction.objects.create(
                task=task,
                user=request.user,
                action=ReviewAction.Action.REJECT,
                reason="Declined by admin"
            )
            
            count += 1
        
        if count:
            messages.success(request, f"{count} task(s) declined successfully.")
        else:
            messages.info(request, "No pending tasks were selected to decline.")
            
        return redirect('admin:tasks_actionitem_changelist')


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