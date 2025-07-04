# Generated by Django 4.2.23 on 2025-07-02 15:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0003_task_review_fields_and_security_questions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='securityquestion',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='task',
            name='expires_after_h',
            field=models.PositiveSmallIntegerField(default=24, help_text='Hours after creation during which the task is publicly visible for review.'),
        ),
        migrations.AlterField(
            model_name='usersecurityanswer',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
