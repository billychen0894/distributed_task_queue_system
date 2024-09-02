from rest_framework import status, viewsets, filters, generics
from .models import Task
from .serializers import (
    TaskSerializer,
    TaskDependencySerializer,
    TaskDependencyCreateSerializer,
)
from .queue_manager import QueueManager
from rest_framework.response import Response
from rest_framework.decorators import action
from django.urls import reverse
from django.db import transaction
from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
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


# Get all dependencies for a task
# Add dependencies to a task
class TaskDependencyList(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TaskDependencyCreateSerializer
        return TaskDependencySerializer

    def get_queryset(self):
        task_id = self.kwargs.get("task_id")
        # Get all dependencies for the given task id
        # using filter instead of get to avoid raising an error if the task id is not found, and it is performant than get because it doesn't need to fetch the task instance
        return Task.objects.filter(dependent_tasks__id=task_id)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        task_id = self.kwargs.get("task_id")
        context["task"] = get_object_or_404(Task, id=task_id)
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        task = self.get_serializer_context()["task"]
        dependency_id = serializer.validated_data["dependency_id"]
        dependency_task = get_object_or_404(Task, id=dependency_id)

        try:
            task.add_dependency(dependency_task)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            TaskDependencySerializer(dependency_task).data,
            status=status.HTTP_201_CREATED,
        )


# Remove a dependency from a task
class TaskDependencyDetail(generics.DestroyAPIView):
    queryset = Task.objects.all()
    permission_classes = [IsAuthenticated]

    # Get the dependency task instance
    def get_object(self):
        task = get_object_or_404(Task, id=self.kwargs.get("task_id"))
        return get_object_or_404(task.dependencies, id=self.kwargs.get("dependency_id"))

    def destroy(self, request, *args, **kwargs):
        dependency_task = self.get_object()
        task = get_object_or_404(Task, id=self.kwargs.get("task_id"))
        task.dependencies.remove(dependency_task)
        return Response(status=status.HTTP_204_NO_CONTENT)
