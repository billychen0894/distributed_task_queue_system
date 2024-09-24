import pika
from django.conf import settings
from .models import Task


def check_rabbitmq_connection():
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=settings.RABBITMQ_HOST,
                port=settings.RABBITMQ_PORT,
                virtual_host=settings.RABBITMQ_VIRTUAL_HOST,
                credentials=pika.PlainCredentials(
                    settings.RABBITMQ_USERNAME, settings.RABBITMQ_PASSWORD
                ),
            )
        )
        connection.close()
        return True
    except:
        return False


def check_database_connection():
    try:
        Task.objects.first()
        return True
    except:
        return False
