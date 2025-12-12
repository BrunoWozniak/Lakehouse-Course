# Building a Data Lakehouse from Scratch

**The Complete Guide to a Production-Ready Open Source Lakehouse**

This guide takes you from zero to a fully operational Data Lakehouse with proper naming conventions, Iceberg tables via Nessie, and data quality checks via Soda.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Technology Stack](#2-technology-stack)
3. [Data Sources](#3-data-sources)
4. [Folder Structure](#4-folder-structure)
5. [Step-by-Step Setup](#5-step-by-step-setup)
6. [Dremio-Nessie-MinIO Integration](#6-dremio-nessie-minio-integration)
7. [Bronze Layer](#7-bronze-layer)
8. [Silver Layer](#8-silver-layer)
9. [Gold Layer](#9-gold-layer)
10. [Soda Data Quality](#10-soda-data-quality)
11. [Dagster Orchestration](#11-dagster-orchestration)
12. [Superset Visualization](#12-superset-visualization)
13. [Naming Conventions](#13-naming-conventions)
14. [Troubleshooting](#14-troubleshooting)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA LAKEHOUSE ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│   │  RAW     │    │  BRONZE  │    │  SILVER  │    │   GOLD   │             │
│   │  FILES   │───▶│  LAYER   │───▶│  LAYER   │───▶│  LAYER   │             │
│   │ CSV/JSON │    │ Parquet  │    │  Clean   │    │  Aggs    │             │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘             │
│        │               │               │               │                    │
│        ▼               ▼               ▼               ▼                    │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │                         MinIO (S3)                               │      │
│   │   lakehouse/bronze/     lakehouse/silver/    lakehouse/gold/    │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │                      Nessie (Iceberg Catalog)                    │      │
│   │            Git-like versioning for table metadata                │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │                      Dremio (Query Engine)                       │      │
│   │              SQL queries across all medallion layers             │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                    │                                        │
│              ┌─────────────────────┼─────────────────────┐                 │
│              ▼                     ▼                     ▼                  │
│        ┌──────────┐         ┌──────────┐         ┌──────────┐             │
│        │  Dagster │         │ Superset │         │  Soda    │             │
│        │ Orchestr │         │    BI    │         │ Quality  │             │
│        └──────────┘         └──────────┘         └──────────┘             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### The Medallion Architecture

| Layer | Purpose | Format | Example |
|-------|---------|--------|---------|
| **Bronze** | Raw data, no transformation | Parquet/Iceberg | `bronze/ecoride/customers/` |
| **Silver** | Cleaned, typed, deduplicated | Iceberg tables | `silver.ecoride_customers` |
| **Gold** | Business aggregations | Iceberg views | `gold.customer_lifetime_value` |

---

## 2. Technology Stack

| Component | Technology | Version | Port | Purpose |
|-----------|------------|---------|------|---------|
| Object Storage | MinIO | latest | 9000, 9001 | S3-compatible data lake storage |
| Iceberg Catalog | Nessie | latest | 19120 | Git-like table versioning |
| Query Engine | Dremio OSS | latest | 9047, 31010, 32010 | SQL analytics on lakehouse |
| Transformations | dbt-core | 1.10+ | - | SQL-based ELT |
| dbt Adapter | dbt-dremio | 1.10+ | - | Dremio connectivity for dbt |
| Orchestration | Dagster | 1.12+ | 3000 | Pipeline scheduling |
| Data Quality | Soda Core | latest | - | Data validation |
| Visualization | Superset | 3.1.0 | 8088 | BI dashboards |
| Notebooks | JupyterLab | latest | 8888 | Interactive analysis |

---

## 3. Data Sources

Your EV company has **7 data sources** across **3 domains**:

### EcoRide (Vehicle Sales)
| File | Format | Records | Description |
|------|--------|---------|-------------|
| `ecoride_customers.csv` | CSV | ~2,500 | Customer information |
| `ecoride_sales.csv` | CSV | ~1,000 | Vehicle sales transactions |
| `ecoride_vehicles.csv` | CSV | ~50 | Vehicle catalog |
| `ecoride_product_reviews.jsonl` | JSONL | ~500 | Customer reviews |

### ChargeNet (Charging Infrastructure)
| File | Format | Records | Description |
|------|--------|---------|-------------|
| `chargenet_stations.jsonl` | JSONL | ~100 | Charging station locations |
| `chargenet_charging_sessions.jsonl` | JSONL | ~10,000 | Charging session logs |

### VehicleHealth (Fleet Diagnostics)
| File | Format | Records | Description |
|------|--------|---------|-------------|
| `vehicle_health_data.jsonl` | JSONL | ~50,000 | Vehicle diagnostics |

---

## 4. Folder Structure

```
lakehouse/
├── data/                           # Raw data files
│   ├── ecoride_customers.csv
│   ├── ecoride_sales.csv
│   ├── ecoride_vehicles.csv
│   ├── ecoride_product_reviews.jsonl
│   ├── chargenet_stations.jsonl
│   ├── chargenet_charging_sessions.jsonl
│   ├── vehicle_health_data.jsonl
│   └── convert_json_to_jsonl.py    # Conversion utility
│
├── transformation/
│   ├── silver/                     # Silver dbt project
│   │   ├── models/
│   │   │   ├── ecoride/           # EcoRide silver models
│   │   │   ├── chargenet/         # ChargeNet silver models
│   │   │   └── vehicle_health/    # VehicleHealth silver models
│   │   ├── dbt_project.yml
│   │   ├── profiles.yml
│   │   └── sources.yml
│   │
│   └── gold/                       # Gold dbt project
│       ├── models/
│       │   ├── ecoride/           # EcoRide gold models
│       │   ├── chargenet/         # ChargeNet gold models
│       │   └── vehicle_health/    # VehicleHealth gold models
│       ├── dbt_project.yml
│       ├── profiles.yml
│       └── sources.yml
│
├── orchestration/                  # Dagster pipeline
│   ├── orchestration/
│   │   ├── assets.py              # Bronze, Silver, Gold assets
│   │   ├── definitions.py         # Jobs and resources
│   │   └── constants.py           # dbt paths
│   ├── setup.py
│   └── pyproject.toml
│
├── soda/                          # Soda data quality
│   ├── configuration.yml          # Soda connection config
│   └── checks/
│       ├── bronze_checks.yml
│       ├── silver_checks.yml
│       └── gold_checks.yml
│
├── docker/
│   ├── dagster/Dockerfile
│   └── superset/
│       ├── Dockerfile
│       └── superset_config.py
│
├── docker-compose.yml
├── README.md
├── DAY3_GUIDE.md
└── LAKEHOUSE_FROM_SCRATCH.md      # This file
```

---

## 5. Step-by-Step Setup

### Step 1: Start Infrastructure

```bash
# Start all services
docker compose up -d

# Verify all services are running
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

Expected services:
- `minio` - Object storage
- `nessie` - Iceberg catalog
- `dremio` - Query engine
- `dagster` - Orchestration
- `superset` - BI dashboards
- `jupyterlab` - Notebooks

### Step 2: Configure MinIO

1. Open MinIO Console: http://localhost:9001
2. Login: `minio` / `minioadmin`
3. Create bucket: `lakehouse`
4. Verify bucket exists

### Step 3: Configure Dremio

1. Open Dremio: http://localhost:9047
2. Create admin account on first visit (use `dremio` / `dremio123`)
3. Add data sources (see Section 6)

### Step 4: Run the Pipeline

1. Open Dagster: http://localhost:3000
2. Click "Assets" to see all data assets
3. Click "Materialize all" to run the full pipeline

### Step 5: Connect Superset

1. Open Superset: http://localhost:8088
2. Login: `admin` / `admin`
3. Add Dremio connection (see Section 12)

---

## 6. Dremio-Nessie-MinIO Integration

This is the **critical** setup that enables Iceberg tables with versioning.

### Understanding the Integration

```
Dremio ──────▶ Nessie Catalog ──────▶ MinIO Storage
              (metadata)              (data files)
```

- **Nessie** stores table metadata (schema, partitions, snapshots)
- **MinIO** stores actual Parquet/Iceberg data files
- **Dremio** queries both through the Nessie catalog

### Step 6.1: Add Nessie Catalog to Dremio

1. In Dremio, go to **"Add Data Source"**
2. Select **"Nessie"** (or "Arctic" in newer versions)
3. Configure:

```
Name: catalog
Nessie Endpoint URL: http://nessie:19120/api/v1
Authentication: None

Storage Settings:
  AWS Root Path: lakehouse
  AWS Access Key: minio
  AWS Secret Key: minioadmin

Connection Properties:
  fs.s3a.endpoint: minio:9000
  fs.s3a.path.style.access: true
  dremio.s3.compat: true
```

4. Click **"Save"**

### Step 6.2: Add MinIO as S3 Source

For reading raw Bronze data:

1. Add new source: **"Amazon S3"**
2. Configure:

```
Name: minio
AWS Access Key: minio
AWS Secret Key: minioadmin

Advanced Options:
  Enable compatibility mode: true
  Root Path: /

Connection Properties:
  fs.s3a.endpoint: minio:9000
  fs.s3a.path.style.access: true
```

### Step 6.3: Verify Connection

In Dremio SQL editor:
```sql
-- List Nessie branches
SELECT * FROM NESSIE_BRANCH('catalog');

-- List tables in catalog
SHOW TABLES IN catalog;
```

---

## 7. Bronze Layer

### Purpose
Raw data ingestion using a **two-stage process** that creates proper Apache Iceberg tables with full metadata, versioning, and time-travel capabilities.

### Two-Stage Bronze Architecture

```
Stage 1: Staging (Parquet)          Stage 2: Iceberg Tables
─────────────────────────           ─────────────────────────
CSV/JSONL files                     Dremio CTAS
       │                                   │
       ▼                                   ▼
lakehouse/staging/{domain}/{table}  catalog.bronze.{domain}_{table}
       │                                   │
       └─── Simple Parquet files           └─── Full Iceberg tables
            (temporary landing)                 (versioned, queryable)
```

### Why Two Stages?

1. **Stage 1 (Staging)**: Fast ingestion using PyArrow directly to MinIO
2. **Stage 2 (Iceberg)**: Dremio CTAS creates proper Iceberg tables with:
   - Nessie catalog metadata
   - Snapshot history (time travel)
   - ACID transactions
   - Schema evolution support

### Bronze Ingestion (Dagster Assets)

Two assets in `orchestration/orchestration/assets.py`:

```python
@asset(group_name="bronze")
def bronze_staging(context: AssetExecutionContext) -> MaterializeResult:
    """Stage 1: Upload raw files to MinIO as Parquet (staging area)."""

    tables = [
        ('ecoride', 'customers', 'ecoride_customers.csv'),
        ('ecoride', 'sales', 'ecoride_sales.csv'),
        ('chargenet', 'stations', 'chargenet_stations.jsonl'),
        # ... 7 tables total
    ]

    for domain, table, filename in tables:
        df = read_file(filename)
        path = f"s3a://lakehouse/staging/{domain}/{table}.parquet"
        df.to_parquet(path)


@asset(group_name="bronze", deps=[bronze_staging])
def bronze_iceberg_tables(context: AssetExecutionContext) -> MaterializeResult:
    """Stage 2: Create Iceberg tables via Dremio CTAS."""

    for domain, table in tables:
        staging_source = f'minio.lakehouse.staging."{domain}"."{table}.parquet"'
        iceberg_table = f"catalog.bronze.{domain}_{table}"

        # Drop and recreate for idempotency
        execute_dremio_sql(f"DROP TABLE IF EXISTS {iceberg_table}")
        execute_dremio_sql(f"""
            CREATE TABLE {iceberg_table} AS
            SELECT * FROM {staging_source}
        """)
```

### Resulting Structure

```
MinIO (lakehouse bucket):           Nessie Catalog (catalog.bronze):
─────────────────────────           ─────────────────────────────────
staging/                            catalog.bronze.ecoride_customers
├── ecoride/                        catalog.bronze.ecoride_sales
│   ├── customers.parquet           catalog.bronze.ecoride_vehicles
│   ├── sales.parquet               catalog.bronze.ecoride_product_reviews
│   ├── vehicles.parquet            catalog.bronze.chargenet_stations
│   └── product_reviews.parquet     catalog.bronze.chargenet_charging_sessions
├── chargenet/                      catalog.bronze.vehicle_health_logs
│   ├── stations.parquet
│   └── charging_sessions.parquet
└── vehicle_health/
    └── logs.parquet

bronze/                             ← Iceberg data files (managed by Nessie)
├── ecoride_customers/
│   ├── metadata/
│   └── data/
└── ...
```

---

## 8. Silver Layer

### Purpose
Clean, type-cast, and deduplicate data. Create business-ready tables.

### Naming Convention

| Component | Convention | Example |
|-----------|------------|---------|
| Model file | `{table_name}.sql` | `customers.sql` |
| Model name | snake_case | `ecoride_customers` |
| Columns | snake_case | `customer_id`, `first_name` |
| Folder | Domain name | `ecoride/`, `chargenet/` |

### Silver Models

#### ecoride/customers.sql
```sql
{{ config(
    materialized='table',
    twin_strategy='allow'
) }}

SELECT
    id AS customer_id,
    first_name,
    last_name,
    email,
    city,
    state,
    country
FROM {{ source('ecoride_bronze', 'ecoride_customers') }}
```

#### ecoride/product_reviews.sql
```sql
-- All columns now snake_case
{{ config(materialized='table', twin_strategy='allow') }}

SELECT
    customer_id,
    review_id,
    review_date,
    rating,
    review_text,
    vehicle_model
FROM {{ source('ecoride_bronze', 'ecoride_product_reviews') }}
```

#### vehicle_health/logs.sql
```sql
{{ config(materialized='table', twin_strategy='allow') }}

SELECT
    vehicle_id,
    model,
    manufacturing_year,
    alerts,
    maintenance_history
FROM {{ source('vehicle_health_bronze', 'vehicle_health_logs') }}
```

### Silver sources.yml (Points to Iceberg Tables)

Since Bronze now creates proper Iceberg tables in the Nessie catalog, Silver sources point to `catalog.bronze.*`:

```yaml
version: 2

sources:
  - name: ecoride_bronze
    database: catalog
    schema: bronze
    tables:
      - name: ecoride_customers
      - name: ecoride_sales
      - name: ecoride_vehicles
      - name: ecoride_product_reviews

  - name: chargenet_bronze
    database: catalog
    schema: bronze
    tables:
      - name: chargenet_stations
      - name: chargenet_charging_sessions

  - name: vehicle_health_bronze
    database: catalog
    schema: bronze
    tables:
      - name: vehicle_health_logs
```

### Silver Model Source References

```sql
-- In customers.sql
SELECT * FROM {{ source("ecoride_bronze", "ecoride_customers") }}
-- Resolves to: catalog.bronze.ecoride_customers

-- In stations.sql
SELECT * FROM {{ source("chargenet_bronze", "chargenet_stations") }}
-- Resolves to: catalog.bronze.chargenet_stations
```

---

## 9. Gold Layer

### Purpose
Business aggregations and analytics-ready views.

### Gold Models

| Model | Purpose |
|-------|---------|
| `customer_lifetime_value` | CLV calculations per customer |
| `customer_segmentation` | Behavior-based segments |
| `vehicle_usage_analytics` | Vehicle popularity metrics |
| `charging_station_metrics` | Station performance KPIs |
| `fleet_health_summary` | Fleet maintenance overview |

### Example: customer_lifetime_value.sql
```sql
{{ config(materialized='view') }}

SELECT
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email,
    COUNT(s.sale_id) AS total_purchases,
    SUM(s.sale_price) AS total_spent,
    AVG(s.sale_price) AS avg_purchase_value,
    MIN(s.sale_date) AS first_purchase_date,
    MAX(s.sale_date) AS last_purchase_date,
    DATEDIFF(MAX(s.sale_date), MIN(s.sale_date)) AS customer_tenure_days
FROM {{ ref('customers') }} c
LEFT JOIN {{ ref('sales') }} s ON c.customer_id = s.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name, c.email
```

---

## 10. Soda Data Quality

### Installation

Add to `orchestration/setup.py`:
```python
install_requires=[
    ...
    "soda-core-dremio",
]
```

### Configuration (soda/configuration.yml)

```yaml
data_source lakehouse:
  type: dremio
  host: dremio
  port: 31010
  username: dremio
  password: dremio123
  schema: catalog.silver
```

### Bronze Checks (soda/checks/bronze_checks.yml)

```yaml
# Validate raw data completeness
checks for bronze_ecoride_customers:
  - row_count > 0
  - missing_count(email) < 100

checks for bronze_ecoride_sales:
  - row_count > 0
  - missing_count(customer_id) = 0
```

### Silver Checks (soda/checks/silver_checks.yml)

```yaml
checks for silver_customers:
  - row_count > 0
  - duplicate_count(customer_id) = 0
  - missing_count(email) = 0
  - invalid_count(email) = 0:
      valid format: email

checks for silver_sales:
  - row_count > 0
  - missing_count(customer_id) = 0
  - values in (payment_method) must exist in ('Credit Card', 'Cash', 'Financing', 'Lease')
```

### Gold Checks (soda/checks/gold_checks.yml)

```yaml
checks for gold_customer_lifetime_value:
  - row_count > 0
  - avg(total_spent) > 0
  - max(total_purchases) < 1000  # Sanity check

checks for gold_charging_station_metrics:
  - row_count > 0
  - avg(total_sessions) > 0
```

### Running Soda Checks

```bash
# Run all checks
soda scan -d lakehouse -c soda/configuration.yml soda/checks/

# Run specific layer
soda scan -d lakehouse -c soda/configuration.yml soda/checks/silver_checks.yml
```

### Integrating with Dagster

```python
from dagster import asset, AssetCheckResult

@asset_check(asset=silver_dbt_assets)
def silver_data_quality(context):
    """Run Soda checks after Silver transformation."""
    result = subprocess.run(
        ["soda", "scan", "-d", "lakehouse",
         "-c", "soda/configuration.yml",
         "soda/checks/silver_checks.yml"],
        capture_output=True
    )

    passed = result.returncode == 0
    return AssetCheckResult(passed=passed, metadata={"output": result.stdout})
```

---

## 11. Dagster Orchestration

### Assets Overview

| Asset | Layer | Type | Dependencies |
|-------|-------|------|--------------|
| `bronze_staging` | Bronze (Stage 1) | Python | None |
| `bronze_iceberg_tables` | Bronze (Stage 2) | Python | bronze_staging |
| `silver_*` | Silver | dbt | bronze_iceberg_tables |
| `gold_*` | Gold | dbt | silver_* |

### Jobs

| Job | Description | Use Case |
|-----|-------------|----------|
| `full_lakehouse_pipeline` | Bronze → Silver → Gold | Daily refresh |
| `bronze_ingestion` | Both bronze stages | New data arrival |
| `silver_transformation` | Just Silver | Schema changes |
| `gold_transformation` | Just Gold | Business logic updates |

### Running Dagster

The Dockerfile uses `dagster dev` which runs both webserver and daemon:

```dockerfile
CMD ["dagster", "dev", "-h", "0.0.0.0", "-p", "3000"]
```

**Important:** The daemon is required for job execution. Check daemon health at http://localhost:3000 → Deployment.

### Scheduling (Optional)

```python
from dagster import ScheduleDefinition

daily_pipeline = ScheduleDefinition(
    job=full_pipeline_job,
    cron_schedule="0 6 * * *",  # 6 AM daily
)
```

---

## 12. Superset Visualization

### Connection String

```
dremio+flight://dremio:dremio123@dremio:32010/DREMIO?UseEncryption=false
```

### Key Settings
- Port: **32010** (Flight protocol, not 31010)
- UseEncryption: **false** (for local Docker setup)
- Host inside Docker: **dremio** (not localhost)

### Recommended Dashboards

1. **Customer Analytics**
   - Customer count by region (map)
   - Customer lifetime value distribution
   - Customer segmentation pie chart

2. **Sales Performance**
   - Monthly sales trend
   - Top selling vehicles
   - Payment method breakdown

3. **Charging Network**
   - Station utilization heatmap
   - Average session duration by station type
   - Peak charging hours

4. **Fleet Health**
   - Vehicles by alert status
   - Maintenance backlog
   - Model reliability comparison

---

## 13. Naming Conventions

### Database Objects

| Type | Convention | Example |
|------|------------|---------|
| Database/Catalog | lowercase | `catalog`, `minio` |
| Schema | lowercase | `bronze`, `silver`, `gold` |
| Table | snake_case | `ecoride_customers` |
| Column | snake_case | `customer_id`, `sale_date` |
| View | snake_case | `customer_lifetime_value` |

### File Names

| Type | Convention | Example |
|------|------------|---------|
| Data files | snake_case | `ecoride_customers.csv` |
| dbt models | snake_case | `customers.sql` |
| Config files | snake_case | `dbt_project.yml` |

### MinIO Paths

```
lakehouse/                    # Bucket
├── bronze/                   # Layer
│   ├── ecoride/             # Domain
│   │   └── customers/       # Table
│   └── chargenet/
└── silver/
    └── ...
```

### Avoid

- Dots in schema names: `bronze.ecoride` (use `/` folder structure instead)
- UUIDs in paths: `customers_ae0f9e2b-1483-...` (configure Airbyte properly)
- Mixed case: `CustomerID` (always use `customer_id`)
- Spaces: `My Table` (always use `my_table`)

---

## 14. Troubleshooting

### Dremio can't read Nessie metadata

**Symptom:** "Unable to retrieve metadata" error

**Solution:**
1. Verify Nessie is running: `curl http://localhost:19120/api/v1/trees`
2. Check Dremio source config has correct MinIO credentials
3. Ensure `fs.s3a.path.style.access: true` is set
4. Restart Dremio after config changes

### Superset connection fails

**Symptom:** "Connection refused" or SSL errors

**Solution:**
1. Use port 32010 (Flight), not 31010 or 9047
2. Add `?UseEncryption=false` to connection string
3. Use `dremio` as host (Docker network), not `localhost`

### dbt can't find sources

**Symptom:** "Relation does not exist"

**Solution:**
1. Verify source paths in `sources.yml` match actual MinIO structure
2. Run Bronze ingestion first to create Parquet files
3. Promote tables in Dremio if using direct MinIO source
4. Check Dremio user has permissions to the schema

### Bronze ingestion fails

**Symptom:** "Access Denied" or "Bucket not found"

**Solution:**
1. Create `lakehouse` bucket in MinIO first
2. Verify AWS credentials in environment variables
3. Check MinIO is accessible from the ingestion container

### Soda checks fail

**Symptom:** "Connection refused" to Dremio

**Solution:**
1. Ensure Dremio is running
2. Use port 31010 for JDBC/ODBC connections
3. Verify username/password in `configuration.yml`

---

## Quick Reference

### Service URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| Dremio | http://localhost:9047 | dremio / dremio123 |
| MinIO | http://localhost:9001 | minio / minioadmin |
| Dagster | http://localhost:3000 | No auth |
| Superset | http://localhost:8088 | admin / admin |
| Nessie | http://localhost:19120 | API only |
| JupyterLab | http://localhost:8888 | No auth |

### Useful Commands

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f dagster
docker compose logs -f dremio

# Rebuild a service
docker compose build dagster
docker compose up -d dagster

# Run dbt manually
cd transformation/silver
dbt run --profiles-dir .

# Run Soda checks
soda scan -d lakehouse -c soda/configuration.yml soda/checks/
```

### Superset Connection String
```
dremio+flight://dremio:dremio123@dremio:32010/DREMIO?UseEncryption=false
```

---

**End of Guide**

This document serves as the master reference for building and operating your Data Lakehouse. For day-to-day operations during the course, see [DAY3_GUIDE.md](DAY3_GUIDE.md).
