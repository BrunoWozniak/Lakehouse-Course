# Superset configuration file for Data Lakehouse Course
# This config enables Dremio connectivity via Arrow Flight protocol

import os
from sqlalchemy.dialects import registry

# =============================================================================
# DREMIO CONFIGURATION
# =============================================================================

# Register Dremio dialects with SQLAlchemy
# Note: dremio:// requires pyodbc, dremio+flight:// uses Arrow Flight (recommended)
registry.register("dremio", "sqlalchemy_dremio.base", "DremioDialect")
registry.register("dremio+flight", "sqlalchemy_dremio.flight", "DremioDialect_flight")

# =============================================================================
# SUPERSET CORE SETTINGS
# =============================================================================

# Secret key for signing cookies (use env var in production)
SECRET_KEY = os.environ.get('SUPERSET_SECRET_KEY', 'lakehouse-course-secret-key-2024')

# SQLAlchemy database URI for Superset's metadata
SQLALCHEMY_DATABASE_URI = 'sqlite:////app/superset_home/superset.db'

# Flask-WTF flag for CSRF
WTF_CSRF_ENABLED = True

# Allow all database connections (required for Dremio)
PREVENT_UNSAFE_DB_CONNECTIONS = False

# =============================================================================
# DREMIO ENGINE SPECIFICATION
# =============================================================================

from superset.db_engine_specs.base import BaseEngineSpec

class DremioEngineSpec(BaseEngineSpec):
    """Engine spec for Dremio via Arrow Flight protocol."""

    engine = "dremio"
    engine_name = "Dremio"
    default_driver = "flight"

    # Connection string template shown in UI
    # IMPORTANT: Use port 32010 (Flight) and UseEncryption=false for local setup
    sqlalchemy_uri_placeholder = (
        "dremio+flight://user:password@host:32010/DREMIO?UseEncryption=false"
    )

    # Silence the statement cache warning
    supports_statement_cache = False

    # Time grain expressions for Dremio SQL
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

# =============================================================================
# STARTUP MESSAGE
# =============================================================================

print("""
================================================================================
SUPERSET LAKEHOUSE CONFIG LOADED
================================================================================
Dremio Connection String (copy this exactly):
dremio+flight://dremio:dremio123@dremio:32010/DREMIO?UseEncryption=false
================================================================================
""")