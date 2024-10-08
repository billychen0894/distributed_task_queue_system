# Generated by Django 5.1 on 2024-09-05 01:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task_manager', '0008_task_dependencies_task_is_recurring_task_last_run_at_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='task',
            name='is_recurring',
        ),
        migrations.RemoveField(
            model_name='task',
            name='recurrence_interval',
        ),
        migrations.AddField(
            model_name='task',
            name='recurrence_type',
            field=models.CharField(choices=[('none', 'None'), ('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')], default='none', max_length=20),
        ),
    ]
