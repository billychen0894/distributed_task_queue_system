from rest_framework import serializers
from .models import Task
from django.utils import timezone
import pytz
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TaskSerializer(serializers.ModelSerializer):
    TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.common_timezones]
    # result field is a serializer method field that calls the get_result method on the Task instance
    result = serializers.SerializerMethodField()

    dependencies = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Task.objects.all(),
        pk_field=serializers.UUIDField(format="hex_verbose"),
    )

    user_timezone = serializers.ChoiceField(choices=TIMEZONE_CHOICES, default="UTC")

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "status",
            "priority",
            "result",
            "retry_count",
            "max_retries",
            "created_at",
            "updated_at",
            "dependencies",
            "scheduled_at",
            "user_timezone",
            "recurrence_type",
            "last_run_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "created_at",
            "updated_at",
            "retry_count",
            "max_retries",
            "result",
            "last_run_at",
            "is_recurring",
            "recurrence_interval",
        ]

    def get_result(self, obj):
        return obj.get_result()

    # Validate dependencies to prevent circular dependencies
    def validate_dependencies(self, data):
        if "dependencies" in data:
            # Get the task instance whether it is being created or updated
            task = self.instance if self.instance else Task(**data)
            for dependency in data["dependencies"]:
                if task.has_circular_dependency(dependency):
                    raise serializers.ValidationError("Circular dependency detected")
        return data

    def create(self, validated_data):
        user_timezone = validated_data.get("user_timezone", "UTC")
        scheduled_at = validated_data.get("scheduled_at")

        if scheduled_at:
            # Get user local time zone
            user_tz = pytz.timezone(user_timezone)

            # Remove timezone info from scheduled_at that was automatically added as UTC timezone
            # the schedule_at input value should be user's local time
            naive_local_time = scheduled_at.replace(tzinfo=None)

            # make aware the naive_local_time to the user time zone
            aware_local_time = user_tz.localize(naive_local_time)

            # converting back user time zone back to UTC for scheduled_at
            validated_data["scheduled_at"] = aware_local_time.astimezone(pytz.UTC)

        return super().create(validated_data)


class TaskDependencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "id",
        ]


class TaskDependencyCreateSerializer(serializers.Serializer):
    dependency_id = serializers.UUIDField(format="hex_verbose")

    def validate_dependency_id(self, dependency_id):
        task = self.context["task"]
        try:
            dependency_task = Task.objects.get(id=dependency_id)
        except Task.DoesNotExist:
            raise serializers.ValidationError("Task with this id does not exist")

        if task.has_circular_dependency(dependency_task):
            raise serializers.ValidationError("Circular dependency detected")
        return dependency_id
