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
7. [Airbyte Data Ingestion](#7-airbyte-data-ingestion)
8. [Bronze Layer](#8-bronze-layer)
9. [Silver Layer](#9-silver-layer)
10. [Gold Layer](#10-gold-layer)
11. [Soda Data Quality](#11-soda-data-quality)
12. [Dagster Orchestration](#12-dagster-orchestration)
13. [Superset Visualization](#13-superset-visualization)
14. [Jupyter Notebooks & ML](#14-jupyter-notebooks--ml)
15. [AI Agent with Chainlit](#15-ai-agent-with-chainlit)
16. [Naming Conventions](#16-naming-conventions)
17. [Troubleshooting](#17-troubleshooting)

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
| **Bronze** | Raw data, no transformation | Iceberg tables | `catalog.bronze.customers` |
| **Silver** | Cleaned, typed, deduplicated | Iceberg tables | `catalog.silver.customers` |
| **Gold** | Business aggregations | Iceberg views | `catalog.gold.customer_lifetime_value` |

---

## 2. Technology Stack

| Component | Technology | Version | Port | Purpose |
|-----------|------------|---------|------|---------|
| Object Storage | MinIO | latest | 9000, 9001 | S3-compatible data lake storage |
| Iceberg Catalog | Nessie | latest | 19120 | Git-like table versioning |
| Query Engine | Dremio OSS | latest | 9047, 31010, 32010 | SQL analytics on lakehouse |
| **Data Ingestion** | **Airbyte** | **latest** | **8000** | **EL (Extract & Load) to Bronze** |
| Transformations | dbt-core | 1.10+ | - | SQL-based transformations (Silver/Gold) |
| dbt Adapter | dbt-dremio | 1.10+ | - | Dremio connectivity for dbt |
| Orchestration | Dagster | 1.12+ | 3000 | Pipeline scheduling |
| Data Quality | Soda Core | latest | - | Data validation |
| Visualization | Superset | 3.1.0 | 8088 | BI dashboards |
| Notebooks | JupyterLab | latest | 8888 | Interactive analysis |

### Data Flow Architecture

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  MinIO       │    │   Airbyte    │    │     dbt      │    │   Superset   │
│  (source)    │───▶│  (Ingestion) │───▶│  (Transform) │───▶│    (BI)      │
│  CSV/JSON    │    │   → Bronze   │    │ Silver/Gold  │    │  Dashboards  │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                           │                   │
                           └───────────────────┘
                                 Dagster
                             (Orchestration)
```

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
│   ├── configuration_silver.yml   # Soda config for Silver layer
│   ├── configuration_gold.yml     # Soda config for Gold layer
│   └── checks/
│       ├── silver_checks.yml      # Silver data quality checks (23 checks)
│       ├── gold_checks.yml        # Gold data quality checks (17 checks)
│       ├── demo_checks.yml        # Advanced check examples
│       └── failing_example_checks.yml  # Intentionally failing checks (demo)
│
├── docker/
│   ├── dagster/Dockerfile
│   └── superset/
│       ├── Dockerfile
│       └── superset_config.py
│
├── docker-compose.yml
├── README.md
└── LAKEHOUSE_FROM_SCRATCH.md      # This file
```

---

## 5. Step-by-Step Setup

This section covers **infrastructure verification only**. Once all services are running and accessible, proceed to Section 6 for configuration.

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

### Step 2: Verify All Services Are Accessible

Open each service in your browser and confirm it loads correctly:

| Service | URL | What You Should See | Login Test |
|---------|-----|---------------------|------------|
| **MinIO** | http://localhost:9001 | Login page | `minio` / `minioadmin` |
| **Dremio** | http://localhost:9047 | Setup wizard (first time) or login page | Create `dremio` / `dremio123` |
| **Nessie** | http://localhost:19120/api/v1 | JSON response (REST API) | No login |
| **Dagster** | http://localhost:3000 | Dagster UI | No login (dev mode) |
| **Superset** | http://localhost:8088 | Login page | `admin` / `admin` |
| **JupyterLab** | http://localhost:8888 | Jupyter interface | No token required |

**Checkpoint:** All 6 services accessible before proceeding.

### Step 3: Configure MinIO Buckets & Upload Files

1. Open MinIO Console: http://localhost:9001
2. Login: `minio` / `minioadmin`
3. Create **two buckets**:

| Bucket | Purpose |
|--------|---------|
| `source` | Raw input files (CSV, JSON, JSONL) |
| `lakehouse` | Bronze/Silver/Gold Iceberg tables |

4. Upload source files to the `source` bucket:
   - Navigate to `source` bucket → **Upload**
   - Upload all files from the `data/` folder:
     - `ecoride_customers.csv`
     - `ecoride_sales.csv`
     - `ecoride_vehicles.csv`
     - `ecoride_product_reviews.jsonl`
     - `chargenet_stations.jsonl`
     - `chargenet_charging_sessions.jsonl`
     - `vehicle_health_data.jsonl`

5. Verify both buckets exist and `source` contains your 7 files

### Step 4: Install Airbyte

Airbyte handles **data ingestion** (Extract & Load) from source files to Bronze Iceberg tables.

> **Note:** Airbyte runs separately from the docker-compose stack using `abctl`.

**Installation (macOS/Linux):**
```bash
curl -LsfS https://get.airbyte.com | bash -
```

**Installation (Windows):**
- Requires Docker Desktop with WSL2 enabled
- Download `abctl` from: https://github.com/airbytehq/abctl/releases
- Add to PATH and run from PowerShell

**Start Airbyte:**
```bash
abctl local install
```

This takes 3-5 minutes. It sets up a local Kubernetes-like environment.

**Get credentials:**
```bash
abctl local credentials
```

**Verify:** Open http://localhost:8000 and login with the credentials from above.

**Checkpoint:** Infrastructure setup complete. All 7 services (6 docker-compose + Airbyte) are running and accessible.

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

### Step 6.2: Verify Connection

In Dremio SQL editor:
```sql
-- List Nessie branches
SHOW BRANCHES IN catalog;
```

> **Note:** In Dremio's UI, when you expand the `catalog` source, you'll see branches (like `main`) listed. These are NOT folders you can click into - they're Nessie branches. To query tables on a specific branch, use SQL with `AT BRANCH "main"` syntax. The "folder not found" error when clicking on `main` is expected behavior.

---

## 7. Airbyte Data Ingestion

Airbyte handles **Extract & Load** from source files to Bronze Iceberg tables.

### 7.1 Configure Source (One Source, 7 Streams)

Create a single S3 source with 7 streams (one per file):

1. Go to **Sources** → **+ New source** → Select **S3**
2. Configure the source settings:

| Field | Value |
|-------|-------|
| **Name** | `MinIO Source` |
| **Bucket** | `source` |
| **S3 Endpoint** | `http://host.docker.internal:9000` |
| **AWS Access Key** | `minio` |
| **AWS Secret Key** | `minioadmin` |

3. **Add 7 Streams** (click "Add stream" for each):

| Stream Name | Globs | Format | Validation Policy |
|-------------|-------|--------|-------------------|
| `customers` | `ecoride_customers.csv` | CSV | Wait for Discovery |
| `sales` | `ecoride_sales.csv` | CSV | Wait for Discovery |
| `vehicles` | `ecoride_vehicles.csv` | CSV | Wait for Discovery |
| `product_reviews` | `ecoride_product_reviews.json` | JSONL | Wait for Discovery |
| `stations` | `chargenet_stations.json` | JSONL | Wait for Discovery |
| `charging_sessions` | `chargenet_charging_sessions.json` | JSONL | Wait for Discovery |
| `vehicle_health` | `vehicle_health_data.json` | JSONL | Wait for Discovery |

> **Why simple stream names?** The stream name becomes the table name in the destination. Using short, descriptive names like `customers` instead of `ecoride_customers` creates cleaner table names: `bronze.customers` vs `bronze.ecoride_customers`.

> **Important Settings:**
> - **Delivery Method:** Replicate Records (required for proper data replication)
> - **Validation Policy:** Wait for Discovery (ensures schema detection completes)

4. Click **Set up source**

### 7.2 Configure Destination (S3 Data Lake → Iceberg)

| Field | Value |
|-------|-------|
| **Name** | `Lakehouse` |
| **Catalog Type** | `Nessie` |
| **Nessie Catalog URI** | `http://host.docker.internal:19120/api/v2` |
| **Access Token** | *(leave empty)* |
| **Main Branch Name** | `main` |
| **S3 Bucket Name** | `lakehouse` |
| **S3 Bucket Region** | `us-east-1` |
| **Warehouse Location** | `s3://lakehouse/bronze` |
| **S3 Endpoint** | `http://host.docker.internal:9000` |
| **AWS Access Key ID** | `minio` |
| **AWS Secret Access Key** | `minioadmin` |

### 7.3 Create Connection & Run Sync

Create a single connection from `MinIO Source` to `Lakehouse`:

1. Go to **Connections** → **+ New connection**
2. Select source: `MinIO Source`
3. Select destination: `Lakehouse`
4. **Configure streams:**

| Setting | Value |
|---------|-------|
| **Sync Mode** | Full Refresh \| Overwrite |
| **Namespace** | Custom format: `bronze` |
| **Schedule** | Manual (for initial setup) |

**Advanced Settings:**

| Setting | Value | Why |
|---------|-------|-----|
| **Schema changes** | Propagate field changes only | New columns flow automatically; type changes/deletions flagged for review |
| **Notify on schema changes** | ✅ Enabled | Get alerted when source structure changes |
| **Backfill new columns** | ✅ Enabled | Historical consistency if columns are added |

> **Why Full Refresh | Overwrite?**
> - Best for static source files (CSV/JSON that get replaced entirely)
> - Ensures destination matches source exactly
> - No duplicate data accumulation

5. Click **Set up connection**
6. Click **Sync now** to run the first sync

### 7.4 Understanding Iceberg Versioning

With **Full Refresh | Overwrite**, each sync:
- Replaces table data in the destination
- BUT Iceberg keeps **snapshot history** (time-travel capability)
- AND Nessie keeps **commit history** (git-like versioning)

**What happens in MinIO:**
```
lakehouse/bronze/ecoride_customers/
├── metadata/           # Iceberg metadata (keeps all versions)
│   ├── v1.metadata.json
│   ├── v2.metadata.json  # New version each sync
│   └── ...
└── data/              # Parquet files (accumulate until compaction)
```

**Query historical data in Dremio:**
```sql
-- View table history
SELECT * FROM TABLE(table_history('catalog.bronze.customers'));

-- Time travel to specific snapshot
SELECT * FROM catalog.bronze.customers AT SNAPSHOT '12345';
```

### 7.5 Resulting Tables

After sync completes, you'll have these Iceberg tables:

| Table | Records |
|-------|---------|
| `bronze.customers` | ~2,500 |
| `bronze.sales` | ~1,000 |
| `bronze.vehicles` | ~50 |
| `bronze.product_reviews` | ~500 |
| `bronze.stations` | ~100 |
| `bronze.charging_sessions` | ~10,000 |
| `bronze.vehicle_health` | ~50,000 |

> **Note:** Table names come from the **stream names** you configured in Airbyte. The names above assume you used simple names. If you used names like `ecoride_customers`, your tables will have those names instead.

### 7.6 Scheduling and Re-Sync Behavior

#### Setting Up Scheduled Syncs

For automated data refreshes, configure a schedule in the connection settings:

1. Go to **Connections** → Select your connection
2. Click **Settings** (gear icon)
3. Under **Schedule**, choose:

| Schedule Type | When to Use |
|--------------|-------------|
| **Manual** | Development, on-demand syncs |
| **Scheduled** | Production, regular data updates |
| **Cron expression** | Complex schedules (e.g., `0 6 * * *` = daily at 6 AM) |

**Common schedules:**

| Cron | Frequency |
|------|-----------|
| `0 * * * *` | Every hour |
| `0 */6 * * *` | Every 6 hours |
| `0 6 * * *` | Daily at 6 AM |
| `0 0 * * 0` | Weekly on Sunday |

#### What Happens When You Re-Run a Sync?

With **Full Refresh | Overwrite** mode (our configuration):

```
┌─────────────────────────────────────────────────────────────────┐
│                    RE-SYNC BEHAVIOR                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Source File                    Destination Table               │
│   ───────────────                ─────────────────               │
│                                                                  │
│   customers.csv                  bronze.customers                │
│   (2,500 rows)      ──────►      (2,500 rows)                   │
│                     Sync 1                                       │
│                                                                  │
│   customers.csv                  bronze.customers                │
│   (2,500 rows)      ──────►      (2,500 rows) ← REPLACED        │
│                     Sync 2       + new Iceberg snapshot          │
│                                                                  │
│   customers.csv                  bronze.customers                │
│   (2,600 rows)*     ──────►      (2,600 rows) ← REPLACED        │
│                     Sync 3       + new Iceberg snapshot          │
│                                                                  │
│   * If source file updated with 100 new customers               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Key points:**

| Question | Answer |
|----------|--------|
| **Will it duplicate data?** | No - Full Refresh | Overwrite replaces the entire table |
| **Is it safe to re-run?** | Yes - completely idempotent (same result each time) |
| **What about history?** | Iceberg keeps snapshots - you can time-travel to previous versions |
| **What if source unchanged?** | Table is still replaced, but data is identical |

#### Sync Modes Explained

Airbyte supports different sync modes. We use **Full Refresh | Overwrite** for this course:

| Mode | Behavior | Best For |
|------|----------|----------|
| **Full Refresh \| Overwrite** | Replace entire table each sync | Static files, small datasets |
| **Full Refresh \| Append** | Add all source data to table | Audit logs (accumulate) |
| **Incremental \| Append** | Add only new/changed records | Large datasets with timestamps |
| **Incremental \| Dedupe** | Upsert based on primary key | CDC, database replication |

**Why Full Refresh | Overwrite for this course?**
1. **Simple** - No state tracking, no deduplication logic
2. **Reliable** - Source = Destination, always
3. **Safe** - Can't accumulate duplicates
4. **Fits use case** - CSV/JSON files that get replaced entirely

> **When would you use Incremental?**
> - Database replication with CDC (Change Data Capture)
> - Large datasets where full refresh is too slow
> - Streaming data with timestamps
> - APIs with pagination/cursors

#### Manual vs Scheduled: Best Practice for the Course

| Phase | Recommended | Why |
|-------|-------------|-----|
| **Development** | Manual | Control exactly when syncs run, debug issues |
| **Demo/Teaching** | Manual | Predictable timing for live demos |
| **Production** | Scheduled | Automated, hands-off operation |

For this course, we keep Airbyte on **Manual** schedule and trigger syncs explicitly. This gives you:
- Full control over when Bronze data updates
- No surprise syncs during demos
- Clear cause-and-effect for debugging

When you're ready for production, switch to a scheduled sync (e.g., daily at 6 AM) so your data pipeline runs automatically.

---

## 8. Bronze Layer

### Purpose
The Bronze layer contains **raw data as Iceberg tables**, created by Airbyte syncs. No transformations applied.

### Verify in Dremio

After Airbyte sync completes, verify tables in Dremio:

```sql
-- List all Bronze tables
SHOW TABLES IN catalog.bronze;

-- Sample data from each domain
SELECT * FROM catalog.bronze.customers LIMIT 5;
SELECT * FROM catalog.bronze.stations LIMIT 5;
SELECT * FROM catalog.bronze.vehicle_health LIMIT 5;

-- Check all row counts (use quoted alias to avoid reserved word issues)
SELECT 'customers' AS table_name, COUNT(*) AS "row_count" FROM catalog.bronze.customers
UNION ALL
SELECT 'sales', COUNT(*) FROM catalog.bronze.sales
UNION ALL
SELECT 'vehicles', COUNT(*) FROM catalog.bronze.vehicles
UNION ALL
SELECT 'stations', COUNT(*) FROM catalog.bronze.stations
UNION ALL
SELECT 'charging_sessions', COUNT(*) FROM catalog.bronze.charging_sessions
UNION ALL
SELECT 'product_reviews', COUNT(*) FROM catalog.bronze.product_reviews
UNION ALL
SELECT 'vehicle_health', COUNT(*) FROM catalog.bronze.vehicle_health;
```

> **Note:** If your Airbyte stream names were different (e.g., `ecoride_customers` instead of `customers`), adjust the table names accordingly.

### Bronze Data Characteristics

| Characteristic | Value |
|----------------|-------|
| **Format** | Apache Iceberg |
| **Catalog** | Nessie (branch: `main`) |
| **Namespace** | `bronze` |
| **Transformations** | None (raw data) |
| **Schema** | Inferred from source files |
| **Partitioning** | None (can be added later) |

### Explore Nessie Versioning

Nessie provides **git-like versioning** for your data lakehouse. Run these queries to explore:

#### List Branches
```sql
SHOW BRANCHES IN catalog;
```

**Expected output:**
| type | refName | commitHash |
|------|---------|------------|
| Branch | main | d5d7ec6b1559... |

Just like git, Nessie has a `main` branch by default. You can create feature branches for testing transformations.

#### View Commit History
```sql
SHOW LOG IN catalog;
```

**Expected output (sample):**
| commitHash | authorName | authorTimeStamp | message |
|------------|------------|-----------------|---------|
| d5d7ec6b... | airbyte | 2025-12-15 20:06:43 | Iceberg append against bronze.sales |
| 6b0d0e02... | airbyte | 2025-12-15 20:06:43 | Iceberg commit against table bronze.sales |
| ... | airbyte | ... | Iceberg table created/registered with name bronze.vehicles |
| 95d0e9c4... | airbyte | 2025-12-15 20:06:41 | create namespace bronze |

**What you're seeing:** Reading bottom-to-top, this shows the complete history of your lakehouse:
1. **`create namespace bronze`** - Airbyte created the bronze namespace
2. **`Iceberg table created/registered`** - Each table's schema registered in catalog
3. **`Iceberg commit against table`** - Metadata updates
4. **`Iceberg append against`** - Actual data written to tables

Each commit has a unique hash, author (`airbyte`), timestamp, and message - just like git!

#### View Table Snapshots (Iceberg Time-Travel)
```sql
SELECT * FROM TABLE(table_history('catalog.bronze.customers'));
```

**Expected output:**
| made_current_at | snapshot_id | parent_id | is_current_ancestor |
|-----------------|-------------|-----------|---------------------|
| 2025-12-15 20:06:43 | 8845049523459704226 | 8608797210309356200 | true |

This shows **Iceberg snapshots** (different from Nessie commits):
- **snapshot_id**: Unique identifier for this version of the table
- **parent_id**: Previous snapshot (if not null, there's history!)
- **is_current_ancestor**: Whether this snapshot is in the current lineage

Each Airbyte sync creates new snapshots, enabling time-travel queries.

#### Time-Travel Query Example
```sql
-- Query data as it existed at a specific snapshot (use snapshot_id from table_history)
SELECT * FROM catalog.bronze.customers AT SNAPSHOT '8608797210309356200';

-- Or query at a specific timestamp
SELECT * FROM catalog.bronze.customers
  FOR SYSTEM_TIME AS OF TIMESTAMP '2025-12-15 20:00:00';
```

> **Try it:** Use the `parent_id` from your `table_history` output to see the previous version of the data!

### Why This Matters

| Feature | Benefit |
|---------|---------|
| **Commit History** | Audit trail of all changes |
| **Branching** | Test transformations without affecting production |
| **Time Travel** | Recover from bad data loads, debug issues |
| **Rollback** | Revert to previous state if needed |

---

## 9. Silver Layer

### Purpose

The Silver layer **cleans and standardizes** Bronze data:
- Remove Airbyte metadata columns (`_airbyte_raw_id`, `_airbyte_extracted_at`, etc.)
- Standardize column names to snake_case
- Cast data types (strings to dates, etc.)
- Apply basic data quality fixes (trim whitespace, etc.)

### Development Workflow: Manual dbt → Dagster Integration

**Important:** We run dbt manually first to develop and test transformations, then integrate with Dagster for production orchestration.

| Phase | How | Why |
|-------|-----|-----|
| **Development** | `dbt run` manually | Iterate quickly, debug issues |
| **Production** | Dagster triggers dbt | Automated scheduling, monitoring |

### Why Run dbt Inside the Dagster Container?

```
┌─────────────────────────────────────┐
│         Dagster Container           │
│  ┌─────────────────────────────┐   │
│  │  dbt-core + dbt-dremio     │   │  ← dbt already installed
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │  /app/transformation/       │   │  ← Volume mount from host
│  │    ├── silver/             │   │
│  │    └── gold/               │   │
│  └─────────────────────────────┘   │
│            │                        │
│            ▼ Network: dremio:9047   │
│  ┌─────────────────────────────┐   │
│  │       Dremio Container      │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

**Reasons:**
1. **dbt is pre-installed** - No local Python/pip setup needed
2. **Network access** - Container can reach `dremio:9047` directly (Docker network)
3. **Same environment** - What works manually will work when Dagster triggers it
4. **Volume mount** - Your local `transformation/` folder is mounted at `/app/transformation/`

### Running dbt for Silver Layer

```bash
# 1. Enter the Dagster container
docker-compose exec dagster bash

# 2. Navigate to Silver dbt project
cd /app/transformation/silver

# 3. Verify connection to Dremio
dbt debug

# 4. Run all Silver models
dbt run

# 5. (Optional) Run tests
dbt test
```

**Expected `dbt debug` output:**
```
All checks passed!
```

**Expected `dbt run` output:**
```
Running with dbt=1.x.x
Found 7 models...
1 of 7 OK created table model silver.charging_sessions
2 of 7 OK created table model silver.customers
3 of 7 OK created table model silver.product_reviews
4 of 7 OK created table model silver.sales
5 of 7 OK created table model silver.stations
6 of 7 OK created table model silver.vehicle_health_logs
7 of 7 OK created table model silver.vehicles
Completed successfully
```

**Will this create duplicate data?**

No! Here's why:
- dbt uses `materialized='table'` → Each run **replaces** the table (not appends)
- Iceberg keeps versions as snapshots → Time-travel still available
- Dagster triggers the same dbt commands → Same result, just automated

```
Run 1: Creates catalog.silver.customers (2500 rows)
Run 2: Replaces catalog.silver.customers (2500 rows) ← same data, new snapshot
Run 3: Replaces catalog.silver.customers (2500 rows) ← same data, new snapshot
```

Each run creates a clean table + Iceberg snapshot for history. No duplicates!

### Silver Transformations Explained

Here's what each Silver model does:

#### 1. customers.sql (EcoRide)
**Purpose:** Clean customer data, select business-relevant columns

```sql
{{ config(materialized="table", twin_strategy="allow") }}

SELECT
    id,
    first_name,
    last_name,
    email,
    phone,
    address,
    city,
    state,
    country
FROM {{ source("bronze", "customers") }}
```

**Transformations:**
- Selects only business columns (drops `_airbyte_*` metadata)
- Keeps original column names (already snake_case from CSV)

#### 2. sales.sql (EcoRide)
**Purpose:** Clean sales transactions, fix date formatting

```sql
{{ config(materialized="table", twin_strategy="allow") }}

SELECT
    id,
    customer_id,
    vehicle_id,
    TO_DATE(sale_date, 'MM/DD/YYYY', 1) AS sale_date,
    CAST(sale_price AS DOUBLE) AS sale_price,
    payment_method
FROM {{ source("bronze", "sales") }}
```

**Transformations:**
- Converts `sale_date` from string (MM/DD/YYYY) to proper DATE type
- Casts `sale_price` to DOUBLE for calculations
- The `1` parameter in `TO_DATE` returns NULL on parse errors (safe mode)

#### 3. vehicles.sql (EcoRide)
**Purpose:** Clean vehicle catalog

```sql
{{ config(materialized="table", twin_strategy="allow") }}

SELECT
    id,
    model_name,
    model_type,
    color,
    "year",
    "range",
    battery_capacity,
    charging_time
FROM {{ source("bronze", "vehicles") }}
```

**Transformations:**
- Quotes reserved words (`"year"`, `"range"`) for Dremio compatibility
- Selects only catalog-relevant columns

#### 4. product_reviews.sql (EcoRide)
**Purpose:** Standardize review data from JSON, fix column casing

```sql
{{ config(materialized="table", twin_strategy="allow") }}

SELECT
    CustomerID AS customer_id,
    ReviewID AS review_id,
    CAST("Date" AS DATE) AS review_date,
    Rating AS rating,
    TRIM(BOTH ' ' FROM ReviewText) AS review_text,
    VehicleModel AS vehicle_model
FROM {{ source("bronze", "product_reviews") }}
```

**Transformations:**
- Renames CamelCase columns to snake_case (JSON preserved original naming)
- Casts `Date` string to proper DATE type
- Trims whitespace from `ReviewText`

#### 5. stations.sql (ChargeNet)
**Purpose:** Clean charging station data

```sql
{{ config(materialized="table", twin_strategy="allow") }}

SELECT
    id,
    address,
    city,
    state,
    country,
    station_type,
    number_of_chargers,
    operational_status
FROM {{ source("bronze", "stations") }}
```

**Transformations:**
- Selects location and operational columns
- Drops Airbyte metadata

#### 6. charging_sessions.sql (ChargeNet)
**Purpose:** Clean charging session logs

```sql
{{ config(materialized="table", twin_strategy="allow") }}

SELECT
    id,
    station_id,
    session_duration,
    energy_consumed_kWh,
    charging_rate,
    cost,
    start_time,
    end_time
FROM {{ source("bronze", "charging_sessions") }}
```

**Transformations:**
- Selects session metrics columns
- Keeps foreign key relationship to stations

#### 7. vehicle_health_logs.sql (VehicleHealth)
**Purpose:** Standardize vehicle diagnostic data from JSON

```sql
{{ config(materialized="table", twin_strategy="allow") }}

SELECT
    VehicleID AS vehicle_id,
    Model AS model,
    ManufacturingYear AS manufacturing_year,
    Alerts AS alerts,
    MaintenanceHistory AS maintenance_history
FROM {{ source("bronze", "vehicle_health") }}
```

**Transformations:**
- Renames CamelCase columns to snake_case
- Keeps complex fields (alerts, maintenance_history) as strings for Gold layer parsing

### Verify Silver Tables in Dremio

After running `dbt run`, verify your Silver tables:

```sql
-- Check row counts for all Silver tables
SELECT 'customers' AS table_name, COUNT(*) AS "row_count" FROM catalog.silver.customers
UNION ALL SELECT 'sales', COUNT(*) FROM catalog.silver.sales
UNION ALL SELECT 'vehicles', COUNT(*) FROM catalog.silver.vehicles
UNION ALL SELECT 'product_reviews', COUNT(*) FROM catalog.silver.product_reviews
UNION ALL SELECT 'stations', COUNT(*) FROM catalog.silver.stations
UNION ALL SELECT 'charging_sessions', COUNT(*) FROM catalog.silver.charging_sessions
UNION ALL SELECT 'vehicle_health_logs', COUNT(*) FROM catalog.silver.vehicle_health_logs;
```

**Expected Results:**

| table_name | row_count |
|------------|-----------|
| customers | 2,500 |
| sales | 5,800 |
| vehicles | 40 |
| product_reviews | 50 |
| stations | 250 |
| charging_sessions | 12,000 |
| vehicle_health_logs | 3,200 |

### Sample Queries to Explore Silver Data

```sql
-- Check date conversion worked in sales
SELECT id, sale_date, sale_price, payment_method
FROM catalog.silver.sales
LIMIT 5;

-- Verify column renaming in product_reviews
SELECT customer_id, review_id, review_date, rating
FROM catalog.silver.product_reviews
LIMIT 5;

-- Check vehicle health standardization
SELECT vehicle_id, model, manufacturing_year
FROM catalog.silver.vehicle_health_logs
LIMIT 5;
```

### Silver sources.yml Configuration

```yaml
version: 2

sources:
  - name: bronze
    description: "Bronze Iceberg tables from Airbyte sync"
    database: catalog
    schema: bronze
    tables:
      - name: customers
      - name: sales
      - name: vehicles
      - name: product_reviews
      - name: stations
      - name: charging_sessions
      - name: vehicle_health
```

### Understanding twin_strategy

The `twin_strategy="allow"` config is specific to **dbt-dremio**:

```sql
{{ config(materialized="table", twin_strategy="allow") }}
```

When dbt creates a table, it needs to handle the case where the table already exists. The `twin_strategy` controls this:

| Strategy | Behavior |
|----------|----------|
| `allow` | Drop and recreate if exists (standard behavior) |
| `clone` | Use Iceberg clone operation |
| `prevent` | Error if table exists |

We use `allow` for idempotent runs - you can run `dbt run` multiple times safely.

---

## 10. Gold Layer

### Purpose

The Gold layer creates **business-ready analytics tables**:
- Join multiple Silver tables together
- Calculate aggregates and metrics
- Create denormalized views for dashboards
- Apply business logic and segmentation

### Running dbt for Gold Layer

```bash
# 1. Enter the Dagster container (if not already)
docker-compose exec dagster bash

# 2. Navigate to Gold dbt project
cd /app/transformation/gold

# 3. Verify connection
dbt debug

# 4. Run all Gold models
dbt run
```

**Expected `dbt run` output:**
```
Running with dbt=1.x.x
Found 7 models...
1 of 7 OK created table model gold.charging_station_utilization
2 of 7 OK created table model gold.customer_lifetime_value
3 of 7 OK created table model gold.customer_segmentation
4 of 7 OK created table model gold.customers_gold
5 of 7 OK created table model gold.enriched_sales
6 of 7 OK created table model gold.vehicle_health_analysis
7 of 7 OK created table model gold.vehicle_usage
Completed successfully
```

### Gold Transformations Explained

#### 1. customers_gold.sql
**Purpose:** Enriched customer data with derived location fields

```sql
{{ config(materialized="table", twin_strategy="allow") }}

SELECT
    c.id as customer_id,
    c.first_name,
    c.email,
    c.city,
    c.state,
    c.country,
    UPPER(c.country) as country_code,
    CONCAT(c.city, ', ', c.state) as location
FROM {{ source('silver', 'customers') }} c
```

**What it does:**
- Adds `country_code` (uppercase country)
- Creates `location` field combining city + state
- Ready for geographic dashboards

#### 2. customer_lifetime_value.sql
**Purpose:** Calculate spending metrics per customer (CLV analytics)

```sql
{% set nessie_branch = var('nessie_branch', 'main') %}

SELECT
    c.id as customer_id,
    c.first_name,
    c.email,
    SUM(s.sale_price) as total_spent,
    COUNT(s.id) as total_transactions,
    AVG(s.sale_price) as average_transaction_value
FROM {{ source('silver', 'customers') }} AT branch {{ nessie_branch }} c
LEFT JOIN {{ source('silver', 'sales') }} AT branch {{ nessie_branch }} s
    ON c.id = s.customer_id
GROUP BY c.id, c.first_name, c.email
```

**What it does:**
- Joins customers with their sales
- Calculates `total_spent`, `total_transactions`, `average_transaction_value`
- Uses Nessie branch syntax for versioned queries
- Essential for customer value analysis

#### 3. customer_segmentation.sql
**Purpose:** Segment customers by behavior and preferences

```sql
{% set nessie_branch = var('nessie_branch', 'main') %}

SELECT
    c.id as customer_id,
    c.first_name,
    c.email,
    c.city,
    c.state,
    c.country,
    COUNT(s.id) as total_purchases,
    AVG(s.sale_price) as average_purchase_value,
    LISTAGG(DISTINCT v.model_name, ', ') as preferred_models
FROM {{ source('silver', 'customers') }} AT branch {{ nessie_branch }} c
LEFT JOIN {{ source('silver', 'sales') }} AT branch {{ nessie_branch }} s
    ON c.id = s.customer_id
LEFT JOIN {{ source('silver', 'vehicles') }} AT branch {{ nessie_branch }} v
    ON s.vehicle_id = v.id
GROUP BY c.id, c.first_name, c.email, c.city, c.state, c.country
```

**What it does:**
- Three-way join: customers → sales → vehicles
- Aggregates `preferred_models` list per customer
- Enables customer segmentation dashboards

#### 4. enriched_sales.sql
**Purpose:** Denormalized sales view with customer and vehicle details

```sql
{% set nessie_branch = var('nessie_branch', 'main') %}

SELECT
    s.id as sale_id,
    s.sale_date,
    s.sale_price,
    s.payment_method,
    c.first_name as customer_name,
    v.model_name as vehicle_model
FROM {{ source('silver', 'sales') }} AT branch {{ nessie_branch }} s
LEFT JOIN {{ source('silver', 'customers') }} AT branch {{ nessie_branch }} c
    ON s.customer_id = c.id
LEFT JOIN {{ source('silver', 'vehicles') }} AT branch {{ nessie_branch }} v
    ON s.vehicle_id = v.id
```

**What it does:**
- Flattens sales with customer name and vehicle model
- Single table for sales reporting dashboards
- No joins needed in BI tools

#### 5. vehicle_usage.sql
**Purpose:** Vehicle popularity and satisfaction metrics

```sql
{% set nessie_branch = var('nessie_branch', 'main') %}

SELECT
    v.id AS vehicle_id,
    v.model_name,
    v.model_type,
    v."year",
    COUNT(s.id) AS total_sales,
    AVG(pr.rating) AS average_rating
FROM {{ source('silver', 'vehicles') }} AT BRANCH {{ nessie_branch }} v
LEFT JOIN {{ source('silver', 'sales') }} AT BRANCH {{ nessie_branch }} s
    ON v.id = s.vehicle_id
LEFT JOIN {{ source('silver', 'product_reviews') }} AT BRANCH {{ nessie_branch }} pr
    ON v.model_name = pr.vehicle_model
GROUP BY v.id, v.model_name, v.model_type, v."year"
```

**What it does:**
- Joins vehicles with sales counts and review ratings
- Shows which models sell best and have highest ratings
- Key for product analytics

#### 6. charging_station_utilization.sql
**Purpose:** Charging network performance metrics

```sql
{% set nessie_branch = var('nessie_branch', 'main') %}

SELECT
    st.id as station_id,
    st.city,
    st.country,
    st.station_type,
    COUNT(cs.id) as total_sessions,
    AVG(cs.session_duration) as average_duration,
    SUM(cs.energy_consumed_kWh) as total_energy_consumed
FROM {{ source('silver', 'stations') }} AT branch {{ nessie_branch }} st
LEFT JOIN {{ source('silver', 'charging_sessions') }} AT branch {{ nessie_branch }} cs
    ON st.id = cs.station_id
GROUP BY st.id, st.city, st.country, st.station_type
```

**What it does:**
- Aggregates session metrics per station
- Calculates `total_sessions`, `average_duration`, `total_energy_consumed`
- Essential for network capacity planning

#### 7. vehicle_health_analysis.sql
**Purpose:** Fleet health status and maintenance insights

```sql
{% set nessie_branch = var('nessie_branch', 'main') %}

SELECT
    vehicle_id,
    model,
    manufacturing_year,
    alerts,
    maintenance_history,
    CASE
        WHEN alerts IS NOT NULL AND LENGTH(alerts) > 10 THEN 'Needs Attention'
        ELSE 'Healthy'
    END AS health_status
FROM {{ source('silver', 'vehicle_health_logs') }} AT BRANCH {{ nessie_branch }}
```

**What it does:**
- Adds `health_status` derived field based on alerts
- Simple classification: 'Needs Attention' vs 'Healthy'
- Starting point for predictive maintenance

### Verify Gold Tables in Dremio

After running `dbt run`, verify your Gold tables:

```sql
-- Check row counts for all Gold tables
SELECT 'customers_gold' AS table_name, COUNT(*) AS "row_count" FROM catalog.gold.customers_gold
UNION ALL SELECT 'customer_lifetime_value', COUNT(*) FROM catalog.gold.customer_lifetime_value
UNION ALL SELECT 'customer_segmentation', COUNT(*) FROM catalog.gold.customer_segmentation
UNION ALL SELECT 'enriched_sales', COUNT(*) FROM catalog.gold.enriched_sales
UNION ALL SELECT 'vehicle_usage', COUNT(*) FROM catalog.gold.vehicle_usage
UNION ALL SELECT 'charging_station_utilization', COUNT(*) FROM catalog.gold.charging_station_utilization
UNION ALL SELECT 'vehicle_health_analysis', COUNT(*) FROM catalog.gold.vehicle_health_analysis;
```

**Expected Results:**

| table_name | row_count |
|------------|-----------|
| customers_gold | 2,500 |
| customer_lifetime_value | 2,500 |
| customer_segmentation | 2,500 |
| enriched_sales | 5,800 |
| vehicle_usage | 40 |
| charging_station_utilization | 250 |
| vehicle_health_analysis | 3,200 |

### Sample Queries to Explore Gold Data

```sql
-- Top 10 customers by lifetime value
SELECT customer_id, first_name, total_spent, total_transactions
FROM catalog.gold.customer_lifetime_value
ORDER BY total_spent DESC
LIMIT 10;

-- Best-selling vehicle models
SELECT model_name, total_sales, average_rating
FROM catalog.gold.vehicle_usage
ORDER BY total_sales DESC
LIMIT 10;

-- Busiest charging stations
SELECT station_id, city, total_sessions, total_energy_consumed
FROM catalog.gold.charging_station_utilization
ORDER BY total_sessions DESC
LIMIT 10;

-- Fleet health overview
SELECT health_status, COUNT(*) as vehicle_count
FROM catalog.gold.vehicle_health_analysis
GROUP BY health_status;
```

### Gold sources.yml Configuration

```yaml
version: 2

sources:
  - name: silver
    database: catalog
    schema: silver
    tables:
      - name: customers
      - name: sales
      - name: vehicles
      - name: product_reviews
      - name: charging_sessions
      - name: stations
      - name: vehicle_health_logs
```

### Understanding Nessie Branch Syntax

Gold models use Nessie branch syntax for versioned queries:

```sql
FROM {{ source('silver', 'customers') }} AT branch {{ nessie_branch }}
```

This resolves to:
```sql
FROM catalog.silver.customers AT branch main
```

**Why use branches?**
- Query data as of a specific branch/commit
- Test transformations on feature branches
- Roll back to previous versions if needed

The `nessie_branch` variable is set in `dbt_project.yml`:
```yaml
vars:
  nessie_branch: "main"
```

### Medallion Architecture Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TRANSFORMATION FLOW                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   BRONZE (Airbyte)          SILVER (dbt)           GOLD (dbt)               │
│   ──────────────────        ──────────────         ─────────────            │
│   Raw from sources    →     Clean + Type    →      Aggregate                │
│   + Airbyte metadata        - metadata             + Join + Derive          │
│                             + snake_case                                     │
│                             + date casting                                   │
│                                                                              │
│   7 tables                  7 tables               7 tables                  │
│   ~24,000 total rows        ~24,000 total rows     ~16,800 total rows*      │
│                                                                              │
│   * Gold has fewer rows due to aggregation (GROUP BY)                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Soda Data Quality

### What is Soda?

Soda is a **data quality** tool that validates your data against defined rules (checks).

| Product | UI | Cost | Description |
|---------|-----|------|-------------|
| **Soda Core** | No (CLI only) | Free/OSS | What we use |
| **Soda Cloud** | Yes (web dashboard) | Paid SaaS | Optional add-on |

### How Soda Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SODA DATA QUALITY FLOW                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────┐      ┌──────────────┐      ┌──────────────┐             │
│   │  Soda CLI    │ ───▶ │ Configuration│ ───▶ │    Dremio    │             │
│   │  (scan cmd)  │      │    .yml      │      │  via ODBC    │             │
│   └──────────────┘      └──────────────┘      └──────────────┘             │
│          │                                           │                      │
│          ▼                                           ▼                      │
│   ┌──────────────┐                           ┌──────────────┐              │
│   │ Check Files  │                           │  Query Data  │              │
│   │  (SodaCL)    │                           │  Run Checks  │              │
│   └──────────────┘                           └──────────────┘              │
│          │                                           │                      │
│          └─────────────────┬─────────────────────────┘                      │
│                            ▼                                                 │
│                    ┌──────────────┐                                         │
│                    │   Results    │                                         │
│                    │ Pass / Fail  │                                         │
│                    └──────────────┘                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why Soda isn't in docker-compose

**Soda is a Python package, not a running service.** Unlike Dremio, MinIO, or Superset (which run continuously), Soda is a CLI tool that executes on-demand.

It's installed inside the Dagster container via the orchestration package.

### Installation Requirements

The Dagster container includes:
- `soda-core-dremio` - Soda with Dremio connector
- `unixodbc` + `unixodbc-dev` - ODBC driver manager
- Dremio Arrow Flight SQL ODBC Driver (extracted from RPM)

> **Note:** Dremio only provides the ODBC driver as an RPM package. The Dockerfile extracts it using `rpm2cpio` for Debian-based containers.

### Configuration Files

Soda requires **separate configuration files for each schema** because the `schema` setting is applied to all checks in a scan.

#### Silver Configuration (soda/configuration_silver.yml)
```yaml
data_source lakehouse:
  type: dremio
  driver: Arrow Flight SQL ODBC Driver
  host: dremio
  port: "32010"
  username: dremio
  password: dremio123
  schema: catalog.silver
  use_encryption: "false"
```

#### Gold Configuration (soda/configuration_gold.yml)
```yaml
data_source lakehouse:
  type: dremio
  driver: Arrow Flight SQL ODBC Driver
  host: dremio
  port: "32010"
  username: dremio
  password: dremio123
  schema: catalog.gold
  use_encryption: "false"
```

> **Important:** Port `32010` is Dremio's Arrow Flight port. The `port` and `use_encryption` values must be quoted strings due to Soda-Dremio connector requirements.

### Silver Checks (soda/checks/silver_checks.yml)

```yaml
checks for customers:
  - row_count > 0:
      name: Customers table has data
  - duplicate_count(id) = 0:
      name: No duplicate customer IDs
  - missing_count(email) = 0:
      name: All customers have email
  - invalid_count(email) = 0:
      name: All emails are valid format
      valid format: email

checks for sales:
  - row_count > 0:
      name: Sales table has data
  - missing_count(customer_id) = 0:
      name: All sales have customer reference
  - min(sale_price) >= 0:
      name: No negative sale prices

checks for charging_sessions:
  - row_count > 0:
      name: Charging sessions has data
  - duplicate_count(id) = 0:
      name: No duplicate session IDs
  - min(energy_consumed_kwh) >= 0:
      name: No negative energy values
```

### Gold Checks (soda/checks/gold_checks.yml)

```yaml
checks for customer_lifetime_value:
  - row_count > 0:
      name: CLV table has data
  - duplicate_count(customer_id) = 0:
      name: No duplicate customers in CLV
  - avg(total_spent) > 0:
      name: Average spending is positive

checks for charging_station_utilization:
  - row_count > 0:
      name: Station utilization has data
  - min(total_sessions) >= 0:
      name: No negative session counts
  - min(total_energy_consumed) >= 0:
      name: No negative energy values

checks for vehicle_health_analysis:
  - row_count > 0:
      name: Health analysis has data
  - invalid_count(health_status) = 0:
      name: Valid health status values
      valid values: ['Healthy', 'Needs Attention']
```

### Running Soda Checks

Run checks from inside the Dagster container:

```bash
# Enter the container
docker-compose exec dagster bash

# Run Silver checks (23 checks)
soda scan -d lakehouse -c /app/soda/configuration_silver.yml /app/soda/checks/silver_checks.yml

# Run Gold checks (17 checks)
soda scan -d lakehouse -c /app/soda/configuration_gold.yml /app/soda/checks/gold_checks.yml
```

**Expected Output:**
```
Soda Core 3.5.6
Scan summary:
23/23 checks PASSED:
    customers in lakehouse
      Customers table has data [PASSED]
      No duplicate customer IDs [PASSED]
      ...
All is good. No failures. No warnings. No errors.
```

### Demo Checks (soda/checks/demo_checks.yml)

Advanced checks demonstrating Soda capabilities:

```yaml
# Freshness check - fails if data too old
checks for catalog.silver.customers:
  - freshness(created_at) < 1d:
      name: Customer data is fresh
      warn: when > 12h
      fail: when > 24h

# Schema validation
  - schema:
      name: Customer table has required columns
      fail:
        when required column missing:
          - id
          - email
          - first_name

# Anomaly detection
checks for catalog.silver.sales:
  - anomaly detection for row_count:
      name: Sales volume is within normal range
      warn: when > 2 stddev
      fail: when > 3 stddev

# Referential integrity
  - values in (customer_id) must exist in catalog.silver.customers (id):
      name: All sales reference valid customers

# Custom SQL check
checks for catalog.silver.product_reviews:
  - failed rows:
      name: No suspiciously short reviews
      fail query: |
        SELECT *
        FROM catalog.silver.product_reviews
        WHERE LENGTH(review_text) < 10
        AND rating = 5
```

### Check Types Reference

| Check Type | Example | Purpose |
|------------|---------|---------|
| `row_count` | `row_count > 0` | Table has data |
| `duplicate_count` | `duplicate_count(id) = 0` | No duplicate values |
| `missing_count` | `missing_count(email) = 0` | No null/empty values |
| `invalid_count` | `invalid_count(email) = 0` with `valid format: email` | Format validation |
| `min`/`max`/`avg` | `min(price) >= 0` | Numeric bounds |
| `freshness` | `freshness(updated_at) < 1d` | Data recency |
| `schema` | Check for required columns | Schema validation |
| `values in` | Cross-table reference check | Referential integrity |
| `failed rows` | Custom SQL query | Complex business rules |

### Dagster Integration

Soda is integrated into Dagster as **assets** that depend on dbt transformations. This creates a visible lineage and automated quality gates.

#### Asset Lineage

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DAGSTER ASSET LINEAGE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────────┐      ┌──────────────────┐                           │
│   │ silver_dbt_assets│─────▶│soda_silver_quality│                           │
│   │   (7 models)     │      │   (23 checks)    │                           │
│   └──────────────────┘      └──────────────────┘                           │
│            │                                                                 │
│            ▼                                                                 │
│   ┌──────────────────┐      ┌──────────────────┐                           │
│   │ gold_dbt_assets  │─────▶│ soda_gold_quality│                           │
│   │   (7 models)     │      │   (17 checks)    │                           │
│   └──────────────────┘      └──────────────────┘                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Available Jobs

| Job | Description | Use When |
|-----|-------------|----------|
| `full_dbt_pipeline` | dbt only (Silver → Gold) | Quick transforms, no validation needed |
| `silver_transformation` | Silver dbt only | Re-run Silver layer |
| `gold_transformation` | Gold dbt only | Re-run Gold layer |
| `full_pipeline_with_quality` | dbt + Soda (complete) | **Production recommended** |
| `silver_with_quality` | Silver + Soda validation | Validate Silver before Gold |
| `gold_with_quality` | Gold + Soda validation | Validate Gold aggregations |
| `quality_checks_only` | Soda only (no dbt) | Ad-hoc quality checks |

#### Running Jobs in Dagster UI

1. Open http://localhost:3000
2. Go to **Overview** → **Jobs**
3. Select `full_pipeline_with_quality`
4. Click **Materialize all**
5. Watch the lineage graph show dbt → Soda execution order

#### Soda Results in Dagster

When Soda runs as a Dagster asset, you get:
- **Metadata** showing checks passed/failed
- **Full output** in the run logs
- **Pipeline failure** if any checks fail (prevents downstream execution)

### Failing Test Example

A failing checks file is provided to demonstrate what happens when data quality issues are detected:

**File:** `soda/checks/failing_example_checks.yml`

```yaml
# These checks are DESIGNED TO FAIL
checks for customers:
  - row_count > 1000000:
      name: "[WILL FAIL] Customers should have over 1 million rows"

checks for sales:
  - min(sale_price) > 100000:
      name: "[WILL FAIL] All sales should be over $100,000"
```

**Run the failing example:**
```bash
docker-compose exec dagster soda scan -d lakehouse \
  -c /app/soda/configuration_silver.yml \
  /app/soda/checks/failing_example_checks.yml
```

**Expected output:**
```
Soda Core 3.5.6
Scan summary:
6/6 checks FAILED:
    customers in lakehouse
      [WILL FAIL] Customers should have over 1 million rows [FAILED]
        check_value: 2500
      [WILL FAIL] Exact impossible row count [FAILED]
        check_value: 2500
    sales in lakehouse
      [WILL FAIL] All sales should be over $100,000 [FAILED]
        check_value: 30001.2
      [WILL FAIL] All sales should be under $100 [FAILED]
        check_value: 99989.27
    charging_sessions in lakehouse
      [WILL FAIL] Table should be empty (it's not) [FAILED]
        check_value: 12000
      [WILL FAIL] Average energy should be impossibly high [FAILED]
        check_value: 15.879333333333333
Oops! 6 failures. 0 warnings. 0 errors. 0 pass.
```

**Key observations:**
- Each failed check shows the actual `check_value`
- Exit code is non-zero (2 = failures found)
- In Dagster, this would halt the pipeline and flag the issue

### Why Use Data Quality Checks?

| Scenario | Without Soda | With Soda |
|----------|--------------|-----------|
| Empty table after ETL bug | Dashboard shows zeros, nobody notices | Pipeline fails, alert sent |
| Duplicates introduced | Reports double-count revenue | Check catches duplicates |
| Invalid data loaded | Users see garbage values | Invalid format check fails |
| Schema drift | Silent column rename breaks joins | Schema check detects change |
| Stale data | Dashboards show old data | Freshness check alerts |

---

## 12. Dagster Orchestration

Dagster orchestrates the dbt transformations (Silver → Gold). Bronze data is ingested separately via Airbyte.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          ORCHESTRATION                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌──────────────┐         ┌─────────────────────────────────────┐  │
│   │   Airbyte    │         │            Dagster                   │  │
│   │  (Manual UI) │         │                                      │  │
│   │              │         │  ┌─────────┐       ┌─────────┐      │  │
│   │  Source CSV  │────────▶│  │ Silver  │──────▶│  Gold   │      │  │
│   │      ↓       │         │  │   dbt   │       │   dbt   │      │  │
│   │   Bronze     │         │  └─────────┘       └─────────┘      │  │
│   │  Iceberg     │         │                                      │  │
│   └──────────────┘         └─────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Why this split?**
- **Airbyte**: Requires its own runtime (abctl/k8s). Adding Dagster-Airbyte integration would require Airbyte always running, adding operational complexity.
- **Dagster**: Orchestrates dbt transformations, which run quickly inside the container.

### 12.1 Assets Overview

Dagster exposes dbt models as **assets** - each dbt model becomes a trackable data asset.

| Asset Group | Layer | Type | Source |
|-------------|-------|------|--------|
| `silver_dbt_assets` | Silver | dbt | Bronze Iceberg tables |
| `gold_dbt_assets` | Gold | dbt | Silver Iceberg tables |

**Code location:** `orchestration/orchestration/assets.py`

```python
@dbt_assets(
    manifest=dbt_silver_manifest_path,
    select="fqn:*",
    name="silver_dbt_assets",
)
def silver_dbt_assets(context: AssetExecutionContext, dbt_silver: DbtCliResource):
    """Transform Bronze → Silver (clean & standardize raw data)"""
    yield from dbt_silver.cli(["build"], context=context).stream()
```

### 12.2 Jobs

Jobs define which assets to materialize together.

| Job | Description | Use Case |
|-----|-------------|----------|
| `full_dbt_pipeline` | Transform Bronze → Silver → Gold | After Airbyte sync completes |
| `silver_transformation` | Transform Bronze → Silver | Re-run Silver only |
| `gold_transformation` | Transform Silver → Gold | Re-run Gold only |

**Code location:** `orchestration/orchestration/definitions.py`

### 12.3 Running the Pipeline

#### Step 1: Access Dagster UI

Open http://localhost:3000

#### Step 2: Navigate to Jobs

Click **Overview** → **Jobs** in the left sidebar.

#### Step 3: Run a Job

1. Click on `full_dbt_pipeline`
2. Click **Materialize all** (top right)
3. Click **Launch Run**

#### Step 4: Monitor Progress

- Watch the run in the **Runs** tab
- Each dbt model shows as a separate step
- Green checkmarks indicate success
- Click any step to see dbt logs

### 12.4 Viewing Assets

The **Catalog** page shows all dbt models as individual assets:

1. Click **Catalog** in the left sidebar
2. See all Silver and Gold models listed
3. Click any asset to view:
   - **Overview** - asset details and metadata
   - **Lineage** - upstream/downstream dependencies (visual graph!)
   - **Runs** - materialization history
   - **Checks** - data quality status

There's also a **Lineage** tab in the top navigation for a global view of all asset dependencies.

### 12.5 Troubleshooting

#### Job Not Appearing?

Dagster needs to reload the code location after changes:

1. Go to **Deployment** → **Code locations**
2. Click the **Reload** button (circular arrow icon)
3. Wait for reload to complete
4. Return to Jobs page

> **Note:** Browser refresh does NOT reload code. You must reload from the Deployment page.

#### dbt Build Failures?

Check the run logs:
1. Go to **Runs**
2. Click the failed run
3. Click the failed step
4. Review the dbt output

Common issues:
- **Source table not found**: Airbyte sync hasn't run yet
- **Syntax errors**: Check dbt model SQL in `transformation/silver/` or `transformation/gold/`

### 12.6 Scheduling (Optional)

For production, add schedules to run dbt after Airbyte syncs complete:

```python
from dagster import ScheduleDefinition

# Run dbt pipeline daily at 7 AM (after 6 AM Airbyte sync)
daily_dbt_schedule = ScheduleDefinition(
    job=full_dbt_pipeline,
    cron_schedule="0 7 * * *",
)

# Add to Definitions
defs = Definitions(
    assets=[...],
    jobs=[...],
    schedules=[daily_dbt_schedule],
)
```

**Tip:** Schedule dbt ~1 hour after Airbyte to ensure sync completes first.

### 12.7 Typical Workflow

```
1. Source data changes (CSV files updated)
           ↓
2. Run Airbyte sync (manual or scheduled)
   → Creates/updates Bronze Iceberg tables
           ↓
3. Run Dagster full_dbt_pipeline
   → Silver transformations (clean data)
   → Gold transformations (aggregations)
           ↓
4. Query in Dremio / Visualize in Superset
```

### 12.8 Verifying Pipeline Execution

After running `full_dbt_pipeline`, verify data was transformed correctly:

```sql
-- Silver layer row counts
SELECT 'customers' AS table_name, COUNT(*) AS "row_count" FROM catalog.silver.customers
UNION ALL SELECT 'sales', COUNT(*) FROM catalog.silver.sales
UNION ALL SELECT 'vehicles', COUNT(*) FROM catalog.silver.vehicles
UNION ALL SELECT 'product_reviews', COUNT(*) FROM catalog.silver.product_reviews
UNION ALL SELECT 'stations', COUNT(*) FROM catalog.silver.stations
UNION ALL SELECT 'charging_sessions', COUNT(*) FROM catalog.silver.charging_sessions
UNION ALL SELECT 'vehicle_health_logs', COUNT(*) FROM catalog.silver.vehicle_health_logs;

-- Gold layer row counts
SELECT 'customers_gold' AS table_name, COUNT(*) AS "row_count" FROM catalog.gold.customers_gold
UNION ALL SELECT 'customer_lifetime_value', COUNT(*) FROM catalog.gold.customer_lifetime_value
UNION ALL SELECT 'customer_segmentation', COUNT(*) FROM catalog.gold.customer_segmentation
UNION ALL SELECT 'enriched_sales', COUNT(*) FROM catalog.gold.enriched_sales
UNION ALL SELECT 'vehicle_usage', COUNT(*) FROM catalog.gold.vehicle_usage
UNION ALL SELECT 'charging_station_utilization', COUNT(*) FROM catalog.gold.charging_station_utilization
UNION ALL SELECT 'vehicle_health_analysis', COUNT(*) FROM catalog.gold.vehicle_health_analysis;
```

### 12.9 Understanding Dagster's Dependency Management

**Why use Dagster instead of just running `dbt run`?**

Dagster provides **dependency-aware orchestration**. Here's how to see it in action:

#### View the Asset Lineage Graph

1. Click **Lineage** in the top navigation bar
2. You'll see a visual graph showing all assets and their dependencies:
   - Silver models depend on Bronze tables
   - Gold models depend on Silver models
   - Hover over assets to see details
   - Click to drill into specific assets

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        ASSET LINEAGE GRAPH                                │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│   Silver Layer                              Gold Layer                    │
│   ────────────                              ──────────                    │
│                                                                           │
│   ┌─────────────────┐                    ┌──────────────────────────┐   │
│   │ silver.customers│──────────────────▶│ gold.customer_lifetime   │   │
│   └─────────────────┘         ┌────────▶│       _value             │   │
│                               │          └──────────────────────────┘   │
│   ┌─────────────────┐         │          ┌──────────────────────────┐   │
│   │ silver.sales    │─────────┼────────▶│ gold.enriched_sales      │   │
│   └─────────────────┘         │          └──────────────────────────┘   │
│                               │                                          │
│   ┌─────────────────┐         │          ┌──────────────────────────┐   │
│   │ silver.vehicles │─────────┴────────▶│ gold.vehicle_usage       │   │
│   └─────────────────┘                    └──────────────────────────┘   │
│                                                                           │
│   ... and so on for all 14 models                                        │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

#### What Dagster Guarantees

| Feature | Benefit |
|---------|---------|
| **Dependency ordering** | Silver always runs before Gold |
| **Partial re-runs** | Re-run only failed assets, skip successful ones |
| **Parallel execution** | Independent assets run concurrently |
| **Run history** | Full audit trail of every materialization |
| **Failure isolation** | One failed model doesn't stop unrelated models |

#### Demo: See Ordering in Action

1. Run `full_dbt_pipeline`
2. Go to **Runs** → click the run
3. Observe the **Gantt chart** view:
   - Silver models start first (left side)
   - Gold models start only after Silver completes (right side)
   - Independent models within a layer run in parallel

#### Compare: Manual dbt vs Dagster

| Approach | Command | Ordering | History | Monitoring |
|----------|---------|----------|---------|------------|
| Manual dbt | `dbt run` | Must run silver/ then gold/ separately | Log files only | None |
| Dagster | Click "Launch Run" | Automatic via asset dependencies | Full UI history | Real-time UI |

### 12.10 Exploring Version History (Nessie + Iceberg)

After running the pipeline multiple times, you now have **multiple snapshots** of your data. This is a key benefit of the Iceberg + Nessie architecture.

#### View Nessie Commit History

In Dremio SQL Runner:

```sql
-- See all commits to the catalog
SHOW LOG AT BRANCH main IN catalog;
```

**Example output after several pipeline runs:**
```
commit_hash                              | author    | message                           | timestamp
─────────────────────────────────────────┼───────────┼───────────────────────────────────┼─────────────────────
a1b2c3d4e5f6...                         | dremio    | CREATE TABLE silver.customers     | 2024-12-15 14:30:00
b2c3d4e5f6a1...                         | dremio    | CREATE TABLE gold.customer_ltv    | 2024-12-15 14:31:00
c3d4e5f6a1b2...                         | dremio    | CREATE TABLE silver.customers     | 2024-12-15 15:45:00
d4e5f6a1b2c3...                         | dremio    | CREATE TABLE gold.customer_ltv    | 2024-12-15 15:46:00
```

Each `dbt run` creates new commits - your data has full Git-like version control!

#### View Table Snapshots (Iceberg)

```sql
-- See all snapshots for a specific table
SELECT * FROM TABLE(table_history('catalog.silver.customers'));
```

**Example output:**
```
made_current_at          | snapshot_id          | parent_id            | is_current
─────────────────────────┼──────────────────────┼──────────────────────┼───────────
2024-12-15 14:30:00      | 1234567890123456789  | NULL                 | false
2024-12-15 15:45:00      | 2345678901234567890  | 1234567890123456789  | true
```

Each snapshot represents a complete version of the table at that point in time.

#### Time-Travel Queries

Query data as it existed at a previous point:

```sql
-- Query customers table from a specific timestamp
SELECT COUNT(*)
FROM catalog.silver.customers
AT TIMESTAMP '2024-12-15 14:30:00';

-- Query customers table from a specific snapshot
SELECT COUNT(*)
FROM catalog.silver.customers
AT SNAPSHOT '1234567890123456789';
```

#### View MinIO Storage (Iceberg Files)

1. Open MinIO Console: http://localhost:9001
2. Navigate to: `lakehouse` bucket → `silver` → `customers`
3. You'll see:
   ```
   lakehouse/
   └── silver/
       └── customers/
           ├── metadata/
           │   ├── v1.metadata.json      ← First version
           │   ├── v2.metadata.json      ← After re-run
           │   └── snap-*.avro           ← Snapshot manifests
           └── data/
               ├── part-00000-*.parquet  ← Data files (v1)
               └── part-00000-*.parquet  ← Data files (v2)
   ```

**Key insight:** Iceberg doesn't delete old data files immediately. They're retained for time-travel until explicitly expired.

#### Why This Matters

| Scenario | How Versioning Helps |
|----------|---------------------|
| **Bad transformation deployed** | Time-travel to query previous version while you fix |
| **Debugging data issues** | Compare current vs historical data |
| **Auditing** | Full history of who changed what, when |
| **A/B testing** | Branch data, test changes, merge if good |
| **Compliance** | Prove data lineage and transformations |

---

## 13. Superset Visualization

### 13.1 Connecting to Dremio

1. Open Superset: http://localhost:8088
2. Login: `admin` / `admin`
3. Go to **Settings** → **Database Connections** → **+ Database**
4. Select **Other**
5. SQLAlchemy URI:
   ```
   dremio+flight://dremio:dremio123@dremio:32010/dremio?UseEncryption=false
   ```
6. Click **Test Connection** → **Connect**

**Key Settings:**
- Port: **32010** (Flight protocol, not 31010)
- UseEncryption: **false** (for local Docker setup)
- Host inside Docker: **dremio** (not localhost)

### 13.2 Creating Datasets

For each Gold table, create a dataset:

1. Go to **Data** → **Datasets** → **+ Dataset**
2. Select the Dremio database
3. Choose schema: `catalog.gold`
4. Select table (e.g., `customer_lifetime_value`)
5. Click **Create Dataset and Create Chart** or just **Add**

**Gold Tables to Add:**
| Dataset | Key Columns |
|---------|-------------|
| `customer_lifetime_value` | customer_id, total_spent, total_transactions |
| `enriched_sales` | sale_date, sale_price, payment_method, vehicle_model |
| `charging_station_utilization` | city, station_type, total_sessions, total_energy_consumed |
| `vehicle_usage` | model_name, total_sales, average_rating |
| `vehicle_health_analysis` | health_status, model, manufacturing_year |
| `customer_segmentation` | state, country, total_purchases |

### 13.3 EcoRide & ChargeNet Dashboard

The dashboard contains charts from multiple Gold tables:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ECORIDE & CHARGENET DASHBOARD                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────────────────────┐  ┌───────────────────────────────┐      │
│  │ Total Revenue (Big Number)    │  │ Customer Count (Big Number)   │      │
│  │ SUM(total_spent)              │  │ COUNT(*)                      │      │
│  └───────────────────────────────┘  └───────────────────────────────┘      │
│                                                                              │
│  ┌───────────────────────────────┐  ┌───────────────────────────────┐      │
│  │ Top Customers by CLV          │  │ Sales by Payment Method       │      │
│  │ Bar: first_name vs total_spent│  │ Pie: payment_method count     │      │
│  └───────────────────────────────┘  └───────────────────────────────┘      │
│                                                                              │
│  ┌───────────────────────────────┐  ┌───────────────────────────────┐      │
│  │ Station Sessions by City      │  │ Energy by Station Type        │      │
│  │ Bar: city vs total_sessions   │  │ Pie: station_type vs energy   │      │
│  └───────────────────────────────┘  └───────────────────────────────┘      │
│                                                                              │
│  ┌───────────────────────────────┐  ┌───────────────────────────────┐      │
│  │ Fleet Health Status           │  │ Customers by State            │      │
│  │ Pie: health_status count      │  │ Bar: state vs customer count  │      │
│  └───────────────────────────────┘  └───────────────────────────────┘      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 13.4 Chart Configuration Reference

| Chart | Dataset | Metric | Dimension |
|-------|---------|--------|-----------|
| Total Revenue | customer_lifetime_value | Simple: SUM(total_spent) | - |
| Customer Count | customer_lifetime_value | Simple: COUNT(*) | - |
| Top Customers | customer_lifetime_value | Simple: SUM(total_spent) | first_name |
| Payment Methods | enriched_sales | Simple: COUNT(*) | payment_method |
| Sessions by City | charging_station_utilization | Simple: SUM(total_sessions) | city |
| Energy by Type | charging_station_utilization | Simple: SUM(total_energy_consumed) | station_type |
| Fleet Health | vehicle_health_analysis | Simple: COUNT(*) | health_status |
| Customers by State | customer_segmentation | Simple: COUNT(*) | state |

**Important:** When adding metrics, use the **Simple** tab (Column + Aggregate) instead of typing SQL directly.

### 13.5 Multi-Table Charts with Dremio Views

Superset datasets are single-table. To create charts that join multiple Gold tables, **create a View in Dremio**.

#### Example: Customer Spending + Vehicle Ratings

```sql
-- Run in Dremio SQL Runner
CREATE OR REPLACE VIEW catalog.gold.customer_vehicle_insights AS
SELECT
    clv.customer_id,
    clv.first_name,
    clv.total_spent,
    clv.total_transactions,
    cs.state,
    cs.country,
    cs.preferred_models
FROM catalog.gold.customer_lifetime_value clv
JOIN catalog.gold.customer_segmentation cs
    ON clv.customer_id = cs.customer_id;
```

#### Example: Sales with Vehicle Ratings

```sql
CREATE OR REPLACE VIEW catalog.gold.sales_with_ratings AS
SELECT
    es.sale_id,
    es.sale_date,
    es.sale_price,
    es.vehicle_model,
    es.customer_name,
    vu.average_rating,
    vu.total_sales as model_total_sales
FROM catalog.gold.enriched_sales es
LEFT JOIN catalog.gold.vehicle_usage vu
    ON es.vehicle_model = vu.model_name;
```

#### Example: Station Performance Summary

```sql
CREATE OR REPLACE VIEW catalog.gold.station_performance AS
SELECT
    csu.city,
    csu.country,
    csu.station_type,
    csu.total_sessions,
    csu.total_energy_consumed,
    csu.average_duration,
    ROUND(csu.total_energy_consumed / NULLIF(csu.total_sessions, 0), 2) as avg_energy_per_session
FROM catalog.gold.charging_station_utilization csu
WHERE csu.total_sessions > 0;
```

#### Using Views in Superset

1. Create the View in Dremio (SQL Runner)
2. In Superset: **Data** → **Datasets** → **+ Dataset**
3. Select Dremio → `catalog.gold` → your new view
4. Create charts using the joined data

#### Example Chart: Price vs Rating Scatter Plot

Using the `sales_with_ratings` view, create a scatter plot to answer: **"Do higher-rated vehicles sell for more?"**

| Setting | Value |
|---------|-------|
| **Chart Type** | Scatter Plot |
| **Dataset** | catalog.gold.sales_with_ratings |
| **X-Axis** | `average_rating` |
| **Y-Axis** | `sale_price` |
| **Series** | `vehicle_model` (colors points by model) |

This chart reveals the correlation between customer ratings and sale prices across different vehicle models - insights only possible by joining two Gold tables.

### 13.6 Dashboard Filters

Dashboard filters work when columns have **matching names** across datasets.

**Compatible filter columns:**
| Filter Column | Works With |
|--------------|------------|
| `country` | customer_segmentation, charging_station_utilization |
| `city` | customer_segmentation, charging_station_utilization |
| `state` | customer_segmentation |
| `health_status` | vehicle_health_analysis |

**Adding a filter:**
1. Edit Dashboard → **+ Filter**
2. Select filter type (e.g., Dropdown)
3. Choose column (e.g., `state`)
4. Enable **"Apply to all charts"**
5. Save

### 13.7 Superset Tips

| Issue | Solution |
|-------|----------|
| Column not found | Sync columns: Edit Dataset → Columns tab → Sync from source |
| Can't limit rows | Use Virtual Dataset with `LIMIT` in SQL |
| Subquery error | Create a Dremio View instead |
| Metric error | Use Simple tab (Column + Aggregate), don't type SQL |
| Chart not updating | Click **Run** or enable Auto-refresh |

---

## 14. Jupyter Notebooks & ML

The JupyterLab service provides an interactive environment for data exploration, machine learning, and advanced analytics.

### 14.1 Accessing JupyterLab

Open http://localhost:8888 (no token required).

### 14.2 Connecting to Dremio

Connect to Dremio via Arrow Flight for high-performance queries:

```python
from pyarrow import flight
import base64
import pandas as pd

# Connect to Dremio
client = flight.connect("grpc://dremio:32010")
auth = base64.b64encode(b"dremio:dremio123").decode()
options = flight.FlightCallOptions(headers=[(b"authorization", f"Basic {auth}".encode())])

# Helper function to query Dremio
def query_dremio(sql: str) -> pd.DataFrame:
    """Execute SQL query and return pandas DataFrame."""
    info = client.get_flight_info(
        flight.FlightDescriptor.for_command(sql), options
    )
    reader = client.do_get(info.endpoints[0].ticket, options)
    return reader.read_pandas()

# Example: Load Gold layer data
df = query_dremio("SELECT * FROM catalog.gold.customer_lifetime_value")
```

### 14.3 Product Reviews Analysis Notebook

The `notebooks/product_reviews_analysis.ipynb` notebook demonstrates text analytics on product reviews, including word clouds and sentiment analysis.

#### What It Does

| Step | Description |
|------|-------------|
| 1. Data Loading | Connects to Dremio and loads product reviews from Silver layer |
| 2. Basic Stats | Review counts and distribution by vehicle model |
| 3. Word Clouds | Visual word frequency analysis per vehicle model |
| 4. Sentiment Analysis | Classifies reviews as positive/negative/neutral using TextBlob |
| 5. Trend Analysis | Sentiment over time and by customer segment |

#### Running the Notebook

1. Open JupyterLab: http://localhost:8888
2. Navigate to `notebooks/product_reviews_analysis.ipynb`
3. Run all cells sequentially (first cell installs wordcloud and textblob)

#### Expected Output

- **Word Clouds**: One per vehicle model showing common review terms
- **Sentiment Charts**: Distribution bar charts (overall, by model, by state, by VIP status)
- **Time Series**: Sentiment trends over time

### 14.4 Customer Segmentation Notebook (Advanced)

The `notebooks/customer_segmentation.ipynb` notebook demonstrates RFM (Recency, Frequency, Monetary) customer segmentation using K-Means clustering.

> **Note**: RFM analysis is a well-established marketing technique developed in the direct mail industry. It's widely used in customer analytics to identify and segment customers based on purchasing behavior. This notebook applies RFM with K-Means clustering for automated customer segmentation.

#### What It Does

| Step | Description |
|------|-------------|
| 1. Data Loading | Connects to Dremio and loads customer/sales data |
| 2. RFM Features | Calculates Recency, Frequency, Monetary values |
| 3. Optimal K | Uses elbow method to find optimal cluster count |
| 4. Clustering | Applies K-Means to segment customers |
| 5. Visualization | 3D scatter plots, radar charts, segment profiles |
| 6. Insights | Business recommendations per segment |

#### RFM Features Explained

| Feature | Description | Calculation |
|---------|-------------|-------------|
| **Recency** | Days since last purchase | `TODAY - last_purchase_date` |
| **Frequency** | Number of orders | `COUNT(orders)` |
| **Monetary** | Total spend | `SUM(revenue)` |

#### Running the Notebook

1. Open JupyterLab: http://localhost:8888
2. Navigate to `notebooks/customer_segmentation.ipynb`
3. Run all cells sequentially
4. Adjust `optimal_k` if needed (default: 4-5 clusters)

#### Expected Output

The notebook generates:
- **5 Customer Segments**: Champions, Loyal, Potential Loyalists, At Risk, Lost
- **Visualizations**: 3D cluster plots, radar charts, distribution histograms
- **Export files**: `customer_segments.csv`, `segment_summary.csv`

### 14.5 Required Libraries

The JupyterLab container includes these libraries (pre-installed):

```
pandas
numpy
scikit-learn
matplotlib
seaborn
plotly
pyarrow
```

---

## 15. AI Agent with Chainlit

A natural language SQL interface powered by LangChain, Mistral AI, and Chainlit. Ask questions in plain English and get SQL-powered answers from your Data Lakehouse.

### Key Features

- **Dynamic schema discovery** - Automatically detects all Gold layer tables and columns at startup
- **SQL transparency** - Shows the generated SQL query alongside results
- **Zero hardcoding** - Uses `SHOW TABLES` and `SELECT * LIMIT 1` to discover schema
- **100% free** - Mistral AI free tier, no credit card required

### 15.1 Architecture

```
User Question (Natural Language)
    ↓
Chainlit UI (http://localhost:8501)
    ↓
LangChain ReAct Agent
    ↓
Mistral Large LLM (FREE tier)
    ↓
SQL Query Generation
    ↓
PyArrow Flight → Dremio
    ↓
Formatted Results + SQL Query
```

### 15.2 Prerequisites

1. **Free Mistral API Key** (required)
2. **Running Dremio** (lakehouse services must be up)

### 15.3 Getting Your Free Mistral API Key

1. Visit https://console.mistral.ai/
2. Sign up (email only, **no credit card required**)
3. Click **"API Keys"** in the left sidebar
4. Click **"Create new key"**
5. Copy the key (starts with `sk-...`)

> **Note**: The free tier has rate limits (~2-5 requests/minute) but is perfect for learning.

### 15.4 Setup

#### Step 1: Configure Environment

```bash
cd agent
cp .env.example .env
```

Edit `.env` and add your Mistral API key:

```
MISTRAL_API_KEY=sk-your-actual-key-here
```

#### Step 2: Start the Agent

```bash
docker-compose up -d lakehouse-agent
```

#### Step 3: Access the UI

Open http://localhost:8501

### 15.5 Available Tables

The agent **automatically discovers** all Gold layer tables at startup. Current tables include:

| Table | Columns |
|-------|---------|
| `catalog.gold.customer_lifetime_value` | customer_id, first_name, email, total_spent, total_transactions, average_transaction_value |
| `catalog.gold.customer_segmentation` | customer_id, first_name, email, city, state, country, total_purchases, average_purchase_value, preferred_models |
| `catalog.gold.customers_gold` | customer_id, first_name, email, city, state, country, country_code, location |
| `catalog.gold.enriched_sales` | sale_id, sale_date, sale_price, payment_method, customer_name, vehicle_model |
| `catalog.gold.charging_station_utilization` | station_id, city, country, station_type, total_sessions, average_duration, total_energy_consumed |
| `catalog.gold.vehicle_health_analysis` | vehicle_id, model, manufacturing_year, alerts, maintenance_history, health_status |
| `catalog.gold.vehicle_usage` | vehicle_id, model_name, model_type, year, total_sales, average_rating |

> **Note**: If you add new Gold layer tables, just restart the agent - it will discover them automatically!

### 15.6 Example Questions

**Customer Analytics:**
- "Show me the top 5 customers by total spent"
- "What's the average transaction value?"
- "How many customers are in each country?"

**Sales Analysis:**
- "What are the total sales by payment method?"
- "Show me sales by vehicle model"

**Charging Network:**
- "Which cities have the most charging sessions?"
- "What's the total energy consumed by station type?"

**Vehicle Fleet:**
- "What vehicles need maintenance?" (health_status = 'Needs Attention')
- "Show vehicles by manufacturing year"

### 15.7 How It Works

1. **Startup**: Agent connects to Dremio, runs `SHOW TABLES IN catalog.gold`, then queries each table to discover columns
2. **Question**: You ask a question in natural language
3. **Reasoning**: LangChain ReAct agent thinks about which table to query
4. **SQL Generation**: Mistral Large generates the SQL query
5. **Execution**: PyArrow Flight sends query to Dremio
6. **Response**: Agent displays the **SQL query** and **formatted results**

> **Note**: No conversation memory - each question is independent. This keeps responses fast and focused.

### 15.8 Files Structure

```
agent/
├── app.py              # Main Chainlit application
├── requirements.txt    # Python dependencies
├── Dockerfile          # → Located at docker/agent/Dockerfile
├── .env.example        # Configuration template
├── .env                # Your configuration (git-ignored)
├── chainlit.md         # Welcome message
└── .gitignore          # Ignores .env and cache
```

### 15.9 Agent Behavior

The agent is configured with strict rules to ensure reliable results:

- **Always uses SQL** - Never answers without executing a query first
- **No hallucination** - If a query fails, it says "I could not retrieve data" instead of making up answers
- **NULL filtering** - Automatically filters NULL values when querying specific fields
- **SQL transparency** - Every response shows the executed SQL query

### 15.10 Troubleshooting

| Issue | Solution |
|-------|----------|
| "MISTRAL_API_KEY not found" | Create `.env` from `.env.example` and add your API key |
| "Initialization Error" | Check Dremio is running: `docker ps \| grep dremio` |
| "Agent stopped due to iteration limit" | Try a simpler question, or use `mistral-large-latest` model |
| Agent timeout / slow | Free tier rate limits - wait 30s between queries |
| "No tables found" | Run the data pipeline first (Bronze → Silver → Gold) |
| Container won't start | Check logs: `docker-compose logs lakehouse-agent` |
| "Format error" | Agent self-corrects - wait for retry |
| Unexpected answer | Check the SQL query shown - does it match your question? |

**Check agent logs:**
```bash
docker-compose logs -f lakehouse-agent
```

**Restart agent after config changes:**
```bash
docker-compose build --no-cache lakehouse-agent
docker-compose up -d lakehouse-agent
```

### 15.11 Technology Stack (100% Free)

| Component | Purpose | Cost |
|-----------|---------|------|
| Mistral Large | LLM for SQL generation | FREE (with rate limits) |
| LangChain | ReAct agent framework | FREE (open source) |
| Chainlit | Chat UI | FREE (open source) |
| PyArrow Flight | High-performance Dremio client | FREE (open source) |
| Dremio | SQL query engine | FREE (open source) |

### 15.12 Configuration Options

Environment variables in `agent/.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `MISTRAL_API_KEY` | (required) | Your Mistral API key |
| `MISTRAL_MODEL` | `mistral-large-latest` | Model to use (alternatives: `open-mixtral-8x22b`, `codestral-latest`) |
| `SCHEMA_PATH` | `catalog.gold` | Schema to query (change to query other layers) |
| `DREMIO_HOST` | `dremio` | Dremio hostname (Docker network) |
| `DREMIO_PORT` | `32010` | Arrow Flight port |

---

## 16. Naming Conventions

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

## 17. Troubleshooting

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

**Symptom:** "Connection refused" or "Can't open lib" error

**Solution:**
1. Ensure Dremio is running
2. Use port **32010** (Arrow Flight), not 31010
3. Verify `port` and `use_encryption` are quoted strings in config
4. Check the ODBC driver was installed (symlink exists at `/opt/arrow-flight-sql-odbc-driver/lib64/libarrow-odbc.so`)
5. Use the correct config file for the layer (`configuration_silver.yml` or `configuration_gold.yml`)

---

## Quick Reference

### Service URLs & Credentials

| Service | URL | Username | Password | Notes |
|---------|-----|----------|----------|-------|
| **MinIO** | http://localhost:9001 | `minio` | `minioadmin` | From `.env` file |
| **Dremio** | http://localhost:9047 | `dremio` | `dremio123` | Create on first visit |
| **Nessie** | http://localhost:19120/api/v1 | - | - | REST API only, no UI |
| **Airbyte** | http://localhost:8000 | *(see below)* | *(see below)* | Run `abctl local credentials` |
| **Dagster** | http://localhost:3000 | - | - | No authentication (dev mode) |
| **Superset** | http://localhost:8088 | `admin` | `admin` | Set in `superset-init.sh` |
| **JupyterLab** | http://localhost:8888 | - | - | No token required |

#### Where Do Credentials Come From?

| Service | Source | How to Change |
|---------|--------|---------------|
| MinIO | `.env` → `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Edit `.env` |
| Dremio | First-time setup wizard | Create any username/password you want |
| Airbyte | Auto-generated by `abctl` | Run `abctl local credentials` to view |
| Superset | `docker-compose.yml` → `SUPERSET_ADMIN_PASSWORD` | Edit docker-compose.yml |

> **Note for Students:** We recommend using the credentials above for consistency with the course materials. If you change them, update the connection strings in Dremio, dbt profiles, Soda configuration, and Airbyte sources accordingly.

### Useful Commands

```bash
# Start docker-compose services
docker compose up -d

# Start Airbyte (separate from docker-compose)
abctl local install       # First time
abctl local credentials   # Get login credentials

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

This document serves as the master reference for building and operating your Data Lakehouse.
