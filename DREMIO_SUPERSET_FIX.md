# Connecting Superset to Dremio - The Right Way

## Understanding the Connection Options

Dremio supports multiple protocols:
- **Flight SQL** (Port 31010) - For high-performance Arrow data transfer
- **ODBC/JDBC** (Port 31010) - Standard SQL connectivity
- **PostgreSQL Wire Protocol** (Port 31010) - PostgreSQL-compatible connections
- **REST API** (Port 9047) - Web UI and REST endpoints

## Option 1: Direct Dremio Connection (If Driver Works)

In Superset, try these connection strings:

### Flight SQL (Recommended for performance):
```
dremio+flight://dremio:dremio123@host.docker.internal:31010/DREMIO
```

### Standard Dremio:
```
dremio://dremio:dremio123@host.docker.internal:31010/DREMIO
```

## Option 2: PostgreSQL Wire Protocol (Fallback)

This is NOT connecting to PostgreSQL! Dremio emulates PostgreSQL protocol:

1. In Superset: Choose **PostgreSQL**
2. This connects to **Dremio** (not Postgres!) via PostgreSQL-compatible protocol
3. Connection details:
   - Host: `host.docker.internal`
   - Port: `31010`
   - Database: `DREMIO`
   - Username: `dremio`
   - Password: `dremio123`

## Option 3: Custom SQLAlchemy URI

Try in "Other" database type:
```
dremio://dremio:dremio123@host.docker.internal:31010/DREMIO
```

## Testing the Connection

Once connected, you should be able to:
1. Browse schemas: `minio.lakehouse."bronze.ecoride"`
2. See your table: `customers_ae0f9e2b-1483-4b02-98c1-bb27e5e135b4`
3. Run queries through Superset's SQL Lab

## Why PostgreSQL Protocol Works

Dremio implements PostgreSQL wire protocol for compatibility:
- Many BI tools already support PostgreSQL
- No special drivers needed
- Same SQL syntax works
- It's still querying Dremio's data lake, not PostgreSQL!

Think of it like speaking English to someone who understands multiple languages - you're still talking to the same person (Dremio), just using a common protocol (PostgreSQL) that both understand.