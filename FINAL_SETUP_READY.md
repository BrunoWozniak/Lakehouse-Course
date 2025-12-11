# Lakehouse Setup - Ready

## Services Running

| Service | URL | Credentials |
|---------|-----|-------------|
| **MinIO** | http://localhost:9001 | minio / minio123 |
| **Dremio** | http://localhost:9047 | dremio / dremio123 |
| **Nessie** | http://localhost:19120 | - |
| **Jupyter** | http://localhost:8888 | token: lakehouse |
| **Superset** | http://localhost:8088 | admin / admin |

## Data Flow

1. Airbyte ingested `ecoride_customers.csv` to MinIO
2. Data stored in `lakehouse/bronze.ecoride/customers_[uuid]/`
3. Dremio connected to MinIO as S3 source
4. dbt customers model working in silver layer

## Working Queries in Dremio

- **Tab 1**: Customer count (shows ~2500 records)
- **Tab 2**: Sample data (LIMIT 20)
- **Tab 3**: City analytics (GROUP BY)

## Quick Verification

```bash
# Check all services are up
docker ps

# Verify MinIO has data
# Browse: http://localhost:9001
# Check: lakehouse bucket → bronze.ecoride folder

# Test Dremio queries
# Open: http://localhost:9047
# Run saved queries in tabs
```

## If Any Service is Down

```bash
# Restart everything
docker-compose down
docker-compose up -d

# Wait 2 minutes for services to initialize
```

## Running dbt

```bash
cd transformation/silver
export DREMIO_USER=dremio
export DREMIO_PASSWORD=dremio123
dbt run --select customers
```

## Superset Connection

Connection string for Dremio:
```
dremio://dremio:dremio123@host.docker.internal:31010/DREMIO
```

## Known Issue

Dremio cannot read through Nessie when using MinIO locally (works with AWS S3/Azure).

**Workaround**: Direct S3 source connection in Dremio (already configured).
