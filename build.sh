#!/usr/bin/env bash
set -euo pipefail

# Install Python deps
pip install -r requirements.txt

# Build React app
cd frontend
npm ci
npm run build
cd ..

# Collect Django/WhiteNoise static files
python manage.py collectstatic --noinput

# Migrate DB
python manage.py migrate --noinput
