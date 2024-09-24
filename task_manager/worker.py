import json
import time
import pika
import logging
from .models import Task
from django.conf import settings
from .queue_manager import QueueManager
from django.utils import timezone
import logging

logger = logging.getLogger("task_manager")


def process_task(task):
    # Simulate processing a task, such as processing data or running a computation
    print(f"Processing task: {task.title}")
    time.sleep(5)
    return "Task completed successfully"


def callback(ch, method, properties, body):
    # Callback function to handle incoming messages from the queue when a new task is received
    task_data = json.loads(body)
    logger.info(f"Received task: {task_data['id']}")

    # Fetch the task from the database
    try:
        task = Task.objects.get(id=task_data["id"])
    except Task.DoesNotExist:
        logger.error(f"Task with id {task_data['id']} not found in the database")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    task.status = Task.STATUS_IN_PROGRESS
    task.save()

    queue_manager = QueueManager()
    # Check if the task is ready to run
    if not task.is_ready_to_run():
        logger.info(f"Task {task.id} is not ready to run")
        # Re-submit task to delay queue
        queue_manager.publish_to_delay_queue(ch, task)
        # Acknowledge original message to remove it from the queue
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    # Check if all dependencies are completed
    dependencies = task.get_all_dependencies()
    if any(dependency.status != Task.STATUS_COMPLETED for dependency in dependencies):
        logger.info(f"Task {task.id} is waiting for dependencies to complete")
        # Requeue the task to later execution
        queue_manager.publish_to_delay_queue(ch, task)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    try:
        result = process_task(task)
        task.status = Task.STATUS_COMPLETED
        task.result = result
        task.last_run_at = timezone.now()
        task.save()

        logger.info(
            "Task processed",
            extra={
                "task_id": task.id,
                "status": task.status,
                "result": task.result,
            },
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)

        # Handle recurring tasks
        if task.is_recurring and task.recurrence_type != "none":
            task.update_next_run_time()

            if not task.is_ready_to_run():
                logger.info(f"Task {task.id} is not ready to run")
                # Re-submit task to delay queue
                queue_manager.publish_to_delay_queue(ch, task)
            else:
                queue_manager.publish_message(task)

        queue_manager.close()
    except Exception as e:
        logger.error(f"Task {task.id} failed: {str(e)}")
        # Retry the task if the maximum number of retries has not been reached
        task.retry_count += 1
        if task.retry_count < task.max_retries:
            task.status = Task.STATUS_QUEUED
            logger.info(
                f"Retrying task {task.id} ({task.retry_count}/{task.max_retries})"
            )
            task.save()
            # Reject the message and requeue it
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        else:
            task.status = Task.STATUS_FAILED
            logger.warning(f"Task {task.id} failed after {task.retry_count} retries")
            task.save()
            ch.basic_ack(delivery_tag=method.delivery_tag)


def start_worker():
    # Start the worker to listen for incoming tasks from the queue
    credentials = pika.PlainCredentials(
        settings.RABBITMQ_USERNAME, settings.RABBITMQ_PASSWORD
    )
    parameters = pika.ConnectionParameters(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        virtual_host=settings.RABBITMQ_VIRTUAL_HOST,
        credentials=credentials,
    )
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(
        queue="task_queue", durable=True, arguments={"x-max-priority": 3}
    )

    # Fair dispatch - one message per worker at a time
    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(queue="task_queue", on_message_callback=callback)

    print("Worker is waiting for tasks. To exit press CTRL+C")

    channel.start_consuming()


if __name__ == "__main__":
    start_worker()
