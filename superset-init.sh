#!/bin/bash
# Superset initialization script for Data Lakehouse Course
# Dremio driver is pre-installed in the Docker image

set -e

echo "=== Waiting for services to be ready ==="
sleep 5

echo "=== Initializing Superset database ==="
superset db upgrade

echo "=== Creating admin user ==="
# Create admin user (username: admin, password: admin)
superset fab create-admin \
    --username admin \
    --firstname Admin \
    --lastname User \
    --email admin@lakehouse.local \
    --password admin || true  # Ignore if user already exists

echo "=== Running Superset init ==="
superset init

echo "=== Starting Superset server ==="
echo ""
echo "============================================================"
echo "SUPERSET READY!"
echo "============================================================"
echo "URL: http://localhost:8088"
echo "Username: admin"
echo "Password: admin"
echo ""
echo "To connect to Dremio, use this connection string:"
echo "dremio+flight://dremio:dremio123@dremio:32010/DREMIO?UseEncryption=false"
echo "============================================================"
echo ""

superset run -h 0.0.0.0 -p 8088

