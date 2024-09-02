from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, TaskDependencyList

router = DefaultRouter()
router.register(r"tasks", TaskViewSet, basename="task")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "tasks/<uuid:task_id>/dependencies/",
        TaskDependencyList.as_view(),
        name="task-dependency-list",
    ),
]
