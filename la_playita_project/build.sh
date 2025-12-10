#!/usr/bin/env bash
# Este script es SOLO para Render.com - NO ejecutar en Windows

set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
