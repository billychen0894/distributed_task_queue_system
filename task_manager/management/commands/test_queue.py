from django.core.management.base import BaseCommand
from task_manager.queue_manager import QueueManager
from task_manager.models import Task


class Command(BaseCommand):
    help = "Test task queue submission"

    def add_arguments(self, parser):
        parser.add_argument("--host", type=str, help="RabbitMQ host")
        parser.add_argument("--port", type=int, help="RabbitMQ port")

    def handle(self, *args, **options):
        # Create a task and add it to the queue
        task = Task.objects.create(
            title="Test Task", description="This is a test task", priority=2
        )

        queue_manager = QueueManager(host=options["host"], port=options["port"])
        queue_manager.connect()
        queue_manager.submit_task(task)
        queue_manager.close()

        self.stdout.write(
            self.style.SUCCESS(f"Successfully submitted task {task.id} to the queue")
        )
