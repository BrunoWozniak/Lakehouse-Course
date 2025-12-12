# Superset image with Dremio connectivity for Data Lakehouse Course
# Uses Arrow Flight protocol for high-performance data transfer

FROM apache/superset:3.1.0

USER root

# Install Dremio driver and dependencies
# - sqlalchemy-dremio: SQLAlchemy dialect for Dremio
# - pyarrow: Required for Arrow Flight protocol
RUN pip install --no-cache-dir \
    sqlalchemy-dremio==3.0.4 \
    pyarrow>=14.0.0

# Copy Superset configuration with Dremio dialect registration
COPY superset_config.py /app/superset_config.py
ENV SUPERSET_CONFIG_PATH=/app/superset_config.py

USER superset