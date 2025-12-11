# Recovery Plan - Making Everything Work for Tomorrow

## Step 1: Clean Up Repository

```bash
# Remove test files we created
rm -f /Users/brunowozniak/Projects/Lakehouse/configure_dremio*.py
rm -f /Users/brunowozniak/Projects/Lakehouse/test_minio*.py
rm -f /Users/brunowozniak/Projects/Lakehouse/emergency*.py
rm -f /Users/brunowozniak/Projects/Lakehouse/demo*.py
rm -f /Users/brunowozniak/Projects/Lakehouse/create*.py
rm -f /Users/brunowozniak/Projects/Lakehouse/direct*.py
rm -f /Users/brunowozniak/Projects/Lakehouse/fix*.py
rm -f /Users/brunowozniak/Projects/Lakehouse/course*.py
rm -f /Users/brunowozniak/Projects/Lakehouse/*.parquet

# Keep only essential docs
# Keep: STUDENT_SETUP_GUIDE.md, docker-compose.yml, data/, transformation/
```

## Step 2: Ingest All 7 Files with Airbyte

### Files to ingest:
1. `ecoride_customers.csv`
2. `ecoride_rides.csv`
3. `ecoride_vehicles.csv`
4. `ecoride_payments.csv`
5. `chargenet_stations.json`
6. `chargenet_sessions.json`
7. `vehicle_health_logs.json`

### For Each File in Airbyte UI:

1. **Create S3 Source** (one per file):
   - Source type: S3
   - Bucket: `source`
   - Glob: `[exact_filename]`
   - Delivery Method: **Replicate Records**
   - For JSON: Reader Options: `{"multiLine": true}`
   - Endpoint: `http://host.docker.internal:9000`
   - Access Key: `minio`
   - Secret Key: `minioadmin`

2. **Create Connection to Lakehouse Destination**:
   - Namespace: `bronze.[company]` (e.g., `bronze.ecoride`)
   - Table Name: Remove prefix (e.g., `customers` not `ecoride_customers`)
   - Primary Key: `id` (or appropriate field)

## Step 3: Make Dremio Work (Without Nessie)

Since Dremio can't read through Nessie, we'll use it as direct S3 source:

### In Dremio:

1. **Use the MinIO S3 source** (already configured)

2. **Promote Parquet Files as Datasets**:
   - Navigate: `minio` → `lakehouse` → `bronze` → `[company]` → `[table]` → `data`
   - Click on folder with Parquet files
   - Look for "Format Folder" icon (folder with arrow)
   - Save as Physical Dataset (PDS)

3. **Create Virtual Datasets (VDS)**:
   ```sql
   -- Create a clean view for each table
   CREATE VDS bronze_customers AS
   SELECT * FROM minio.lakehouse.bronze.[path_to_parquet];

   -- Save in a Space for easy access
   ```

## Step 4: Configure dbt to Use Dremio

### Update dbt profiles.yml:
```yaml
silver:
  outputs:
    dev:
      type: dremio
      threads: 1
      host: localhost
      port: 9047
      user: dremio
      password: dremio123
      database: lakehouse  # Your space name
      schema: silver
  target: dev
```

### Run dbt:
```bash
cd transformation/silver
dbt deps
dbt run

cd ../gold
dbt deps
dbt run
```

## Step 5: Connect Superset to Dremio

### In Superset (http://localhost:8088):

1. **Add Database Connection**:
   - Database type: Other
   - SQLAlchemy URI: `dremio+flight://dremio:dremio123@localhost:31010/dremio`

   Or if Flight doesn't work:
   - Use JDBC: `jdbc:dremio:direct=localhost:31010`

2. **Create Charts**:
   - Use the Virtual Datasets from Dremio
   - Build dashboards

## Step 6: Set Up Orchestration with Dagster

### Why Dagster over Airflow:
- Easier to set up
- Better UI for demos
- Works well with dbt

### Quick Dagster Setup:
```bash
pip install dagster dagster-webserver dagster-dbt dagster-airbyte

# Create dagster project
dagster project scaffold --name lakehouse_orchestration

# Add your dbt and Airbyte as assets
```

### Simple DAG:
```python
from dagster import job, op

@op
def sync_airbyte():
    # Trigger Airbyte sync
    pass

@op
def run_dbt_silver():
    # Run dbt silver models
    pass

@op
def run_dbt_gold():
    # Run dbt gold models
    pass

@job
def lakehouse_pipeline():
    run_dbt_gold(run_dbt_silver(sync_airbyte()))
```

## What You Can Show Tomorrow:

### Hour 1-2: Architecture & Ingestion
- Show Docker containers running
- Demo Airbyte ingesting all 7 files
- Show data landing in MinIO
- Show tables registered in Nessie

### Hour 3-4: Query Engine & SQL
- Show Dremio connecting to MinIO
- Promote datasets from Parquet files
- Create Virtual Datasets
- Run SQL queries

### Hour 5: Transformations
- Run dbt silver models
- Run dbt gold models
- Show data quality improvements

### Hour 6: Visualization
- Connect Superset to Dremio
- Create a simple dashboard
- Show real-time updates

### Hour 7: Orchestration
- Show Dagster UI
- Demonstrate pipeline automation
- Discuss production considerations

## The Bug Explanation:

"Dremio has a known issue with Nessie catalog when using MinIO. The workaround is to query the Parquet files directly from S3, which still gives us full SQL capabilities. In production, you'd use AWS S3 or fix the connector."

## Emergency Backup Plan:

If something doesn't work:
1. Use Jupyter with Pandas to query
2. Show the architecture conceptually
3. Focus on the learning experience
4. Emphasize real-world troubleshooting skills