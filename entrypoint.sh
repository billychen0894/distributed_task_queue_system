#!/bin/sh

set -e

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Create superuser
echo "Creating superuser..."
python manage.py shell << END
from django.contrib.auth.models import User
from django.db import IntegrityError
try:
    User.objects.create_superuser('admin', 'admin@example.com', 'adminpassword')
    print('Superuser created successfully')
except IntegrityError:
    print('Superuser already exists')
END

# Start server
echo "Starting server..."
exec "$@"