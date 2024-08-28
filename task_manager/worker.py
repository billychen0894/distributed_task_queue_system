import json
import time
import pika
from .models import Task
from django.conf import settings


def process_task(task):
    # Simulate processing a task, such as processing data or running a computation
    print(f"Processing task: {task.title}")
    time.sleep(5)
    return True


def callback(ch, method, properties, body):
    # Callback function to handle incoming messages from the queue when a new task is received
    task_data = json.loads(body)
    print(f"Received task: {task_data['id']}")

    # Fetch the task from the database
    task = Task.objects.get(id=task_data["id"])
    task.status = "in_progress"
    task.save()

    try:
        result = process_task(task)

        if result:
            task.status = "completed"
            task.save()
        else:
            raise Exception("Task processing failed")
    except Exception as e:
        task.status = "failed"
        task.save()
        print(f"Task {task.id} failed: {str(e)}")

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
