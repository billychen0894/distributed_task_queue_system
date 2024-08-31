import pika
import json
from django.conf import settings


class QueueManager:
    def __init__(
        self,
        host=None,
        port=None,
        virtual_host=None,
        username=None,
        password=None,
        queue_name="task_queue",
    ):
        self.host = host or settings.RABBITMQ_HOST
        self.port = port or settings.RABBITMQ_PORT
        self.virtual_host = virtual_host or settings.RABBITMQ_VIRTUAL_HOST
        self.username = username or settings.RABBITMQ_USERNAME
        self.password = password or settings.RABBITMQ_PASSWORD
        self.queue_name = queue_name
        self.default_routing_key = queue_name
        self.connection = None
        self.channel = None
        # Note: The connection and channel are created in the constructor, but the connection is not opened until the `connect` method is called, allowing for better flexibility and resource management.

    def connect(self):
        if self.connection is None or self.connection.is_closed:
            credentials = pika.PlainCredentials(self.username, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                virtual_host=self.virtual_host,
                credentials=credentials,
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            self.channel.queue_declare(
                queue=self.queue_name, durable=True, arguments={"x-max-priority": 3}
            )
            self.channel.tx_select()  # Enable transactions for the channel

    def close(self):
        if self.connection and self.connection.is_open:
            self.connection.close()

    # generic method to publish a message to a queue
    def publish_message(self, message, routing_key=None, priority=None):
        try:
            if not self.connection or self.connection.is_closed:
                self.connect()

            if routing_key is None:
                routing_key = self.queue_name

            if not isinstance(message, str):
                message = json.dumps(message)

            properties = pika.BasicProperties(delivery_mode=2)

            if priority is not None:
                properties.priority = priority

            self.channel.basic_publish(
                exchange="",
                routing_key=routing_key,
                body=message,
                properties=properties,
            )

            self.channel.tx_commit()  # Commit the transaction
        except Exception as e:
            self.channel.tx_rollback()  # Rollback the transaction
            raise e

    # explict method to publish a message to the default queue - task_queue
    def submit_task(self, task):
        message = {
            "id": str(task.id),
            "title": task.title,
            "description": task.description,
            "priority": task.priority,
        }

        self.publish_message(message, self.default_routing_key, task.priority)
