from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    
    dependencies = [
        ("tasks", "0002_actionitem_task_auto_approved_task_posted_to_monday_and_more"),
    ]

    operations = [
        # Task new fields
        migrations.AddField(
            model_name="task",
            name="reviewed_at",
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name="task",
            name="rejected_reason",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="task",
            name="expires_after_h",
            field=models.PositiveSmallIntegerField(default=24),
        ),

        # SecurityQuestion model
        migrations.CreateModel(
            name="SecurityQuestion",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("question_text", models.CharField(max_length=255, unique=True)),
            ],
            options={
                "verbose_name": "Security Question",
                "verbose_name_plural": "Security Questions",
            },
        ),

        # UserSecurityAnswer model
        migrations.CreateModel(
            name="UserSecurityAnswer",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="auth.user"),
                ),
                (
                    "question",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="tasks.securityquestion"),
                ),
                ("answer_hash", models.CharField(max_length=128)),
            ],
            options={
                "unique_together": {("user", "question")},
            },
        ),
    ] 