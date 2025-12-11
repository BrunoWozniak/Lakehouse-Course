# Alternative: Connect Superset via PostgreSQL Protocol

Since the Dremio driver has issues, we can use Dremio's PostgreSQL wire protocol support!

## Option 1: PostgreSQL Connection (Recommended)

### In Superset:
1. Go to Settings → Database Connections → + Database
2. Choose **PostgreSQL**
3. Fill in:
   - Host: `host.docker.internal`
   - Port: `31010`
   - Database: `DREMIO`
   - Username: `dremio`
   - Password: `dremio123`
4. Display Name: `Dremio via PostgreSQL`
5. Click TEST CONNECTION → CONNECT

## Option 2: Direct SQLAlchemy URI

Try this PostgreSQL-compatible connection string:
```
postgresql://dremio:dremio123@host.docker.internal:31010/DREMIO
```

## Option 3: Show Superset with Sample Data

If connection doesn't work, you can:
1. Use Superset's example datasets
2. Upload a CSV directly to Superset
3. Show the UI and explain the concept

## What to Tell Students

"Superset supports multiple connection methods. In production, you'd typically use:
- Presto/Trino for large-scale analytics
- PostgreSQL/MySQL for transactional data
- Direct CSV uploads for quick prototypes
- The specific Dremio driver when properly configured in enterprise settings"

## Quick Win Alternative

Upload the CSV directly to Superset:
1. Data → Databases → examples (SQLite)
2. Data → Upload CSV to Database
3. Choose your customers CSV
4. Create charts from uploaded data

This shows the BI capability even if the connection doesn't work!