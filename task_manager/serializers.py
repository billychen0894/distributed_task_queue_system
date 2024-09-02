from rest_framework import serializers
from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    # result field is a serializer method field that calls the get_result method on the Task instance
    result = serializers.SerializerMethodField()

    dependencies = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Task.objects.all()
    )

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
            "schedule_at",
            "is_recurring",
            "recurring_interval",
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
