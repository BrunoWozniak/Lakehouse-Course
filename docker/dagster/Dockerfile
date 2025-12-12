# Dagster image for Data Lakehouse Course
# Includes dbt-dremio and all pipeline dependencies

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy orchestration package
COPY orchestration/ /app/orchestration/

# Copy transformation projects (for dbt)
COPY transformation/ /app/transformation/

# Copy data folder mount point
RUN mkdir -p /data

# Install orchestration package with all dependencies
RUN pip install --no-cache-dir -e /app/orchestration/

# Set environment variables
ENV DAGSTER_HOME=/app/dagster_home
ENV DAGSTER_DBT_PARSE_PROJECT_ON_LOAD=1

# MinIO (S3) credentials
ENV AWS_S3_ENDPOINT=http://minio:9000
ENV AWS_ACCESS_KEY_ID=minio
ENV AWS_SECRET_ACCESS_KEY=minioadmin

# Dremio credentials for dbt
ENV DREMIO_HOST=dremio
ENV DREMIO_USER=dremio
ENV DREMIO_PASSWORD=dremio123

# Data folder path
ENV DATA_FOLDER=/data

# Create dagster home directory
RUN mkdir -p $DAGSTER_HOME

# Set working directory to orchestration project
WORKDIR /app/orchestration

# Expose Dagster webserver port
EXPOSE 3000

# Run Dagster dev (includes webserver + daemon in one process)
# This is simpler for demos - production would use separate containers
CMD ["dagster", "dev", "-h", "0.0.0.0", "-p", "3000"]
