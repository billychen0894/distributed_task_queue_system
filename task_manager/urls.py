from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TaskViewSet,
    TaskDependencyList,
    TaskDependencyDetail,
    TaskExecutionOrder,
)

router = DefaultRouter()
router.register(r"tasks", TaskViewSet, basename="task")

urlpatterns = [
    path(
        "tasks/<uuid:task_id>/dependencies/",
        TaskDependencyList.as_view(),
        name="task-dependency-list",
    ),
    path(
        "tasks/<uuid:task_id>/dependencies/<uuid:dependency_id>/",
        TaskDependencyDetail.as_view(),
        name="task-dependency-detail",
    ),
    path(
        "tasks/execution-order/",
        TaskExecutionOrder.as_view(),
        name="task-execution-order",
    ),
    path("", include(router.urls)),
]
