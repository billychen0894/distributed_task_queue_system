from django.core.management.base import BaseCommand
from task_manager.worker import start_worker


class Command(BaseCommand):
    help = "Start the task worker"

    def handle(self, *args, **options):
        self.stdout.write("Starting task worker...")
        start_worker()
