# Distributed Task Queue System

## Overview

This project is a distributed task queue system built with Django and RabbitMQ. It allows for the creation, management, and execution of tasks with dependencies, priorities, and scheduling capabilities.

## Features

- Task creation and management
- Task dependencies
- Priority-based task execution
- Scheduled tasks
- Recurring tasks
- Health checks for system components
- RESTful API for task operations
- JWT authentication

## Technology Stack

- Django 4.2.7
- Django Rest Framework
- PostgreSQL
- RabbitMQ
- Docker and Docker Compose

## Project Structure

The main components of the project are:

- `task_manager`: The core Django app handling task operations
- `worker.py`: Processes tasks from the queue
- `queue_manager.py`: Manages interactions with RabbitMQ
- `dag_manager.py`: Handles task dependency resolution

## API Endpoints

- `/api/tasks/`: CRUD operations for tasks
- `/api/tasks/<task_id>/dependencies/`: Manage task dependencies
- `/api/tasks/execution-order/`: Get the execution order of tasks
- `/api/health/`: System health check
- `/api/token/`: Obtain JWT token
- `/api/token/refresh/`: Refresh JWT token

## Setup and Installation

1. Clone the repository:
```
git clone https://github.com/billychen0894/distributed_task_queue_system.git
cd distributed_task_queue_system
```
2. Create a `.env` file in the project root (Please refer to `.env.template`)
3. Build and run the Docker containers:
```
docker-compose up --build
```
4. Apply models migrations (This has been automated. Please refer to `entrypoint.sh`)
5. Create a superuser (This has been automated.Please refer to `entrypoint.sh`):

## Usage

1. Access the API at `http://localhost:8000/api/`
2. Use the `/api/token/` endpoint to obtain a JWT token
3. Include the token in the Authorization header for authenticated requests

## Monitoring

- RabbitMQ Management Interface: `http://localhost:15672`
- Django Admin Interface: `http://localhost:8000/admin/`
