from rest_framework import status, viewsets, filters
from .models import Task
from .serializers import TaskSerializer
from .queue_manager import QueueManager
from rest_framework.response import Response
from rest_framework.decorators import action
from django.urls import reverse
from django.db import transaction
from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    # Enables filtering, searching and ordering for the API
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status", "priority"]
    search_fields = ["title", "description"]
    ordering_fields = ["priority", "created_at", "updated_at"]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        queue_manager = QueueManager()
        try:
            with transaction.atomic():
                task = serializer.save(status=Task.STATUS_PENDING)

                # Avoid potential race condition where the task is submitted to the queue before the transaction is committed
                ## and the task is retrieved in queue_manager.submit_task() might be ran in different transaction causing the race condition
                transaction.on_commit(
                    lambda: self._submit_task_to_queue(task, queue_manager)
                )

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
        return Response(data)

    @action(detail=False, methods={"get"})
    def stats(self, request):
        total = Task.objects.count()
        by_status = Task.objects.values("status").annotate(count=Count("status"))
        return Response(
            {
                "total": total,
                "by_status": {item["status"]: item["count"] for item in by_status},
            }
        )

    def _submit_task_to_queue(self, task, queue_manager):
        try:
            queue_manager.submit_task(task)
            task.status = Task.STATUS_QUEUED
            task.save()
        except Exception as e:
            logger.error(f"Failed to submit task to queue: {e}")
