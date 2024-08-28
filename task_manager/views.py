from django.shortcuts import render
from rest_framework import generics
from .models import Task
from .serializers import TaskSerializer
from .queue_manager import QueueManager


class TaskCreateView(generics.CreateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    # This method is called when a new task is created (overridden default behaviour from CreateAPIView)
    def perform_create(self, serializer):
        task = serializer.save()
        queue_manager = QueueManager()
        queue_manager.submit_task(task)
        queue_manager.close()
