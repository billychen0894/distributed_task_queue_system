from rest_framework import status, viewsets
from .models import Task
from .serializers import TaskSerializer
from .queue_manager import QueueManager
from rest_framework.response import Response
from django.urls import reverse
from django.db import transaction


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        queue_manager = QueueManager()
        try:
            with transaction.atomic():
                task = serializer.save(status=Task.STATUS_PENDING)
                queue_manager.submit_task(task)

                task.status = Task.STATUS_QUEUED
                task.save()

                headers = self.get_success_headers(serializer.data)
                if not headers and task.id:
                    location = reverse("task-detail", kwargs={"pk": str(task.id)})
                    headers["Location"] = request.build_absolute_uri(location)

                return Response(
                    serializer.data, status=status.HTTP_201_CREATED, headers=headers
                )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            queue_manager.close()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        data["result"] = instance.get_result()
        return Response(data)
