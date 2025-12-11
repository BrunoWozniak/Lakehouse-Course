# Lakehouse Architecture - Reference Guide

## Service URLs & Credentials

| Service | URL | Username | Password |
|---------|-----|----------|----------|
| **Dremio** | http://localhost:9047 | dremio | dremio123 |
| **MinIO** | http://localhost:9001 | minio | minio123 |
| **Nessie** | http://localhost:19120 | - | - |
| **Jupyter** | http://localhost:8888 | - | token: lakehouse |
| **Superset** | http://localhost:8088 | admin | admin |

---

## Quick Start

```bash
# Start all services
docker-compose up -d

# Verify services are running
docker ps
```

---

## Current Status

### Working Components

1. **MinIO**: Storing data in `lakehouse` bucket
2. **Dremio**: SQL queries via direct S3 source connection
3. **Nessie**: Catalog running (known compatibility issue with Dremio/MinIO)
4. **Jupyter**: Ready for Python/Spark exploration
5. **Superset**: UI accessible with Dremio driver installed
6. **dbt**: Silver layer transformation for customers model working

### Data Available

Currently only **customers** data is ingested via Airbyte:
- Location: `minio.lakehouse."bronze.ecoride".customers_ae0f9e2b-1483-4b02-98c1-bb27e5e135b4.data`
- Records: ~2500 customers

Other data sources (vehicles, sales, product_reviews, chargenet, vehicle_health) are defined in dbt but not yet ingested.

---

## Known Issues

### Dremio + Nessie + MinIO Compatibility

Dremio cannot resolve `s3a://` paths through Nessie when using MinIO locally.

**Error**: `"http: Name or service not known"`

**Workaround**: Connect Dremio directly to MinIO as an S3 source (already configured).

**Note**: This issue does not occur with AWS S3 or Azure in production environments.

---

## Dremio Queries

```sql
-- Customer Count
SELECT COUNT(*) as total_customers
FROM minio.lakehouse."bronze.ecoride".customers_ae0f9e2b-1483-4b02-98c1-bb27e5e135b4.data

-- Sample Data
SELECT *
FROM minio.lakehouse."bronze.ecoride".customers_ae0f9e2b-1483-4b02-98c1-bb27e5e135b4.data
LIMIT 20

-- City Analytics
SELECT city, COUNT(*) as customer_count
FROM minio.lakehouse."bronze.ecoride".customers_ae0f9e2b-1483-4b02-98c1-bb27e5e135b4.data
GROUP BY city
ORDER BY customer_count DESC
```

---

## dbt Transformations

### Running dbt

```bash
cd transformation/silver
export DREMIO_USER=dremio
export DREMIO_PASSWORD=dremio123

# Run customers model
dbt run --select customers
```

### Source Configuration

The customers source is configured in `transformation/silver/models/sources.yml`:
- Database: `minio`
- Schema: `lakehouse."bronze.ecoride"."customers_ae0f9e2b-1483-4b02-98c1-bb27e5e135b4"`
- Table identifier: `data`

Other sources are defined as placeholders for future data ingestion.

---

## Superset Connection

### Connecting to Dremio

1. Go to **Settings** → **Database Connections**
2. Click **+ Database** → Choose **Other**
3. Use connection string:
   ```
   dremio://dremio:dremio123@host.docker.internal:31010/DREMIO
   ```
4. Display Name: `Dremio Lakehouse`
5. Under **Advanced** → **SQL Lab**: Enable "Allow DML" and "Expose database in SQL Lab"
6. Click **TEST CONNECTION** then **CONNECT**

---

## Data Flow

```
CSV/JSON files → Airbyte → MinIO (Iceberg) → Dremio (SQL) → Superset (Viz)
                                    ↓
                              dbt (Transformations)
```

---

## Files Reference

- `docker-compose.yml` - Service orchestration
- `transformation/silver/` - dbt silver layer models
- `transformation/gold/` - dbt gold layer models
- `docker/superset/` - Custom Superset configuration
- `simple_ingestion/` - Data ingestion service
