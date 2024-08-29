import json
import time
import pika
import logging
from .models import Task
from django.conf import settings


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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

    task.status = "in_progress"
    task.save()

    try:
        result = process_task(task)
        task.status = "completed"
        task.result = result
        task.save()
        logger.info(f"Task {task.id} completed successfully")
    except Exception as e:
        logger.error(f"Task {task.id} failed: {str(e)}")
        task.status = "failed"
        task.save()

    # Acknowledge the message
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
