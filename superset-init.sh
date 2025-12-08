#!/bin/bash

# Wait for the database to be ready
sleep 10

# Install necessary packages
pip install --no-cache-dir sqlalchemy-dremio

# Initialize the database
superset db upgrade

# Create an admin user (replace the values as needed)
superset fab create-admin \
              --username admin \
              --firstname Admin \
              --lastname User \
              --email admin@example.com \
              --password admin

# Initialize Superset
superset init

# Start the Superset server
superset run -h 0.0.0.0 -p 8088

