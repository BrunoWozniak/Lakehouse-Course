# Dagster image for Data Lakehouse Course
# Includes dbt-dremio and all pipeline dependencies

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
# - git: for dbt package management
# - unixodbc: required by Soda for Dremio ODBC connection
# - curl: for downloading Dremio ODBC driver
# - rpm2cpio/cpio: for extracting RPM packages (Dremio only provides .rpm, not .deb)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    unixodbc \
    unixodbc-dev \
    curl \
    rpm2cpio \
    cpio \
    && rm -rf /var/lib/apt/lists/*

# Install Dremio Arrow Flight SQL ODBC Driver
# Dremio only provides .rpm packages (x86_64 only), so we extract it manually
RUN curl -L -o /tmp/dremio-odbc.rpm \
    https://download.dremio.com/arrow-flight-sql-odbc-driver/arrow-flight-sql-odbc-driver-LATEST.x86_64.rpm \
    && cd /tmp \
    && rpm2cpio dremio-odbc.rpm | cpio -idmv \
    && mv /tmp/opt/arrow-flight-sql-odbc-driver /opt/ \
    && rm -rf /tmp/dremio-odbc.rpm /tmp/opt \
    && cd /opt/arrow-flight-sql-odbc-driver/lib64 \
    && ln -s libarrow-odbc.so.* libarrow-odbc.so

# Configure ODBC driver
RUN echo "[Arrow Flight SQL ODBC Driver]\n\
Description=Dremio Arrow Flight SQL ODBC Driver\n\
Driver=/opt/arrow-flight-sql-odbc-driver/lib64/libarrow-odbc.so" > /etc/odbcinst.ini

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
