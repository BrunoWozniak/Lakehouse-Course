# Superset configuration file
import os
from sqlalchemy.dialects import registry

# Register Dremio dialect with SQLAlchemy
registry.register("dremio", "sqlalchemy_dremio.base", "DremioDialect")
registry.register("dremio+flight", "sqlalchemy_dremio.flight", "DremioDialect_flight")

# Secret key for signing cookies
SECRET_KEY = os.environ.get('SUPERSET_SECRET_KEY', 'your-secret-key-here')

# SQLAlchemy database URI
SQLALCHEMY_DATABASE_URI = 'sqlite:////app/superset_home/superset.db'

# Flask-WTF flag for CSRF
WTF_CSRF_ENABLED = True

# Add Dremio to supported databases
PREVENT_UNSAFE_DB_CONNECTIONS = False

# Register Dremio engine spec for Superset
from superset.db_engine_specs.base import BaseEngineSpec

class DremioEngineSpec(BaseEngineSpec):
    engine = "dremio"
    engine_name = "Dremio"
    default_driver = ""
    sqlalchemy_uri_placeholder = "dremio://user:password@host:31010/dremio"

    _time_grain_expressions = {
        None: "{col}",
        "PT1S": "DATE_TRUNC('second', {col})",
        "PT1M": "DATE_TRUNC('minute', {col})",
        "PT1H": "DATE_TRUNC('hour', {col})",
        "P1D": "DATE_TRUNC('day', {col})",
        "P1W": "DATE_TRUNC('week', {col})",
        "P1M": "DATE_TRUNC('month', {col})",
        "P3M": "DATE_TRUNC('quarter', {col})",
        "P1Y": "DATE_TRUNC('year', {col})",
    }

print("Superset config loaded - Dremio dialect and engine spec registered!")