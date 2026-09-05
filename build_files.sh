#!/bin/bash
echo "Installing pip and dependencies..."
python3 -m ensurepip --upgrade || true
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo "Collecting static files..."
python3 manage.py collectstatic --noinput --clear
