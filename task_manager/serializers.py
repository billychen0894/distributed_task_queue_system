from rest_framework import serializers
from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    # result field is a serializer method field that calls the get_result method on the Task instance
    result = serializers.SerializerMethodField()

    dependencies = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Task.objects.all(),
        pk_field=serializers.UUIDField(format="hex_verbose"),
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
            "scheduled_at",
            "is_recurring",
            "recurrence_interval",
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
