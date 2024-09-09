from django.db import models
import uuid
from datetime import timedelta
from django.utils import timezone
import pytz
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Task(models.Model):
    STATUS_PENDING = "pending"
    STATUS_QUEUED = "queued"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    PRIORITY_CHOICES = (
        (1, "Low"),
        (2, "Medium"),
        (3, "High"),
    )

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("queued", "Queued"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    )

    RECURRENCE_TYPE_CHOICES = (
        ("none", "None"),
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
    )

    TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.common_timezones]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2)
    result = models.TextField(blank=True, null=True)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    user_timezone = models.CharField(
        max_length=50, choices=TIMEZONE_CHOICES, default="UTC"
    )
    recurrence_type = models.CharField(
        max_length=20, choices=RECURRENCE_TYPE_CHOICES, default="none"
    )
    last_run_at = models.DateTimeField(null=True, blank=True)
    # A task can have multiple dependencies and a dependency can be shared by multiple tasks
    dependencies = models.ManyToManyField(
        "self", symmetrical=False, related_name="dependent_tasks"
    )

    def __str__(self):
        return self.title

    def get_result(self):
        if self.status == "completed":
            return self.result
        elif self.status == "failed":
            return f"Task failed after {self.retry_count} retries"
        else:
            return f"Task is {self.status}"

    # Check if the task has a circular dependency: preventing infinite loops
    def has_circular_dependency(self, task):
        if task == self:
            return True
        for dependency in task.dependencies.all():
            if self.has_circular_dependency(dependency):
                return True
        return False

    # Add a dependency to the current task
    def add_dependency(self, dependency_task):
        if not self.has_circular_dependency(dependency_task):
            self.dependencies.add(dependency_task)
        else:
            raise ValueError(
                "Adding this dependency would cause a circular dependency."
            )

    # Get all direct and indirect dependencies of current task
    def get_all_dependencies(self):
        all_dependencies = set()
        for dependency in self.dependencies.all():
            all_dependencies.add(dependency)
            all_dependencies.update(dependency.get_all_dependencies())
        return all_dependencies

    # Check if the task is ready to run
    def is_ready_to_run(self):
        now = timezone.now()
        logger.info(f"Task {self.id}: Checking if ready to run")
        logger.info(f"Task {self.id}: Scheduled at: {self.scheduled_at}")
        logger.info(f"Task {self.id}: Now: {now}")

        if self.scheduled_at is None:
            logger.info(f"Task {self.id}: No scheduled time, task is ready to run")
            return True

        time_difference = (self.scheduled_at - now).total_seconds()

        if time_difference > 0:
            logger.info(f"Task {self.id}: Task is not ready to run yet")
            return False
        else:
            logger.info(f"Task {self.id}: Task is ready to run")
            return True

    # Update the next run time of the task
    def update_next_run_time(self):
        if self.is_recurring and self.recurrence_interval:
            self.scheduled_at = timezone.now() + self.recurrence_interval
            self.save()

    # @property
    # def is_recurring(self):
    #     return self.recurrence_type != "none"

    # @property
    # def recurrence_interval(self):
    #     if self.recurrence_type == "daily":
    #         return timedelta(days=1)
    #     elif self.recurrence_type == "weekly":
    #         return timedelta(weeks=1)
    #     elif self.recurrence_type == "monthly":
    #         return timedelta(days=30)
    #     return None
