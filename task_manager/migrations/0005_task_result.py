# Generated by Django 5.1 on 2024-08-29 02:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task_manager', '0004_task_priority'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='result',
            field=models.TextField(blank=True, null=True),
        ),
    ]
