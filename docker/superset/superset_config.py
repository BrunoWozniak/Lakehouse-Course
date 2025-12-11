# Superset configuration file
import os
from sqlalchemy.dialects import registry

# Register Dremio dialect
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

print("Superset config loaded - Dremio dialect registered!")