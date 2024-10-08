# Generated by Django 5.1 on 2024-08-31 00:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task_manager', '0006_task_max_retries_task_retry_count'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('queued', 'Queued'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=20),
        ),
    ]
