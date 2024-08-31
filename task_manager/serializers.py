from rest_framework import serializers
from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    # result field is a serializer method field that calls the get_result method on the Task instance
    result = serializers.SerializerMethodField()

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
        ]
        read_only_fields = [
            "id",
            "status",
            "created_at",
            "updated_at",
            "retry_count",
            "max_retries",
            "result",
        ]

    def get_result(self, obj):
        return obj.get_result()
