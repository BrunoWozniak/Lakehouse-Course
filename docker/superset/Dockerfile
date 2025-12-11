FROM apache/superset:latest

USER root

# Install additional drivers
RUN pip install --no-cache-dir \
    psycopg2-binary \
    pyarrow \
    sqlalchemy-dremio==3.0.4

# Copy sqlalchemy-dremio to the venv (Superset uses venv, not system packages)
RUN cp -r /usr/local/lib/python3.10/site-packages/sqlalchemy_dremio* /app/.venv/lib/python3.10/site-packages/ || true

# Create initialization script to register Dremio dialect
RUN echo "from sqlalchemy.dialects import registry; \
registry.register('dremio', 'sqlalchemy_dremio.base', 'DremioDialect'); \
registry.register('dremio+flight', 'sqlalchemy_dremio.flight', 'DremioDialect_flight')" \
> /app/pythonpath/register_dremio.py

USER superset