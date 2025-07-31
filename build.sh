#!/usr/bin/env bash

echo "🐍 Installing Python dependencies..."
pip install -r requirements.txt

echo "🗃️ Applying database migrations..."
python manage.py migrate

echo "🧼 Collecting static files..."
python manage.py collectstatic --noinput
