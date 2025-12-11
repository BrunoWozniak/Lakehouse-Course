FROM apache/superset:latest

USER root

# Install additional drivers
RUN pip install --no-cache-dir \
    psycopg2-binary \
    pyarrow \
    sqlalchemy-dremio==3.0.4

# Copy sqlalchemy-dremio to the venv (Superset uses venv, not system packages)
RUN cp -r /usr/local/lib/python3.10/site-packages/sqlalchemy_dremio* /app/.venv/lib/python3.10/site-packages/ || true

# Copy custom config
COPY superset_config.py /app/superset_config.py
ENV SUPERSET_CONFIG_PATH /app/superset_config.py

USER superset