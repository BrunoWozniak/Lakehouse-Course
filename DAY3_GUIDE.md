# Day 3: Production Readiness

Welcome to Day 3! Today we bring everything together with orchestration (Dagster), visualization (Superset), and data quality (Soda).

---

## Schedule Overview

### Morning Session (9:00 - 12:30)

| Time | Duration | Topic |
|------|----------|-------|
| 09:00 | 30 min | Recap Day 1-2 + Today's Agenda |
| 09:30 | 45 min | **Part 1**: Dremio Setup & Verification |
| 10:15 | 15 min | ☕ **BREAK** |
| 10:30 | 60 min | **Part 2**: Dagster Orchestration Deep Dive |
| 11:30 | 60 min | **Part 3**: Running the Full Pipeline |

### Afternoon Session (13:30 - 17:00)

| Time | Duration | Topic |
|------|----------|-------|
| 13:30 | 30 min | **Part 4**: Exploring Results in Dremio |
| 14:00 | 45 min | **Part 5**: Superset Setup & Connection |
| 14:45 | 15 min | ☕ **BREAK** |
| 15:00 | 60 min | **Part 6**: Building Dashboards |
| 16:00 | 30 min | **Part 7**: Data Quality with Soda |
| 16:30 | 30 min | **Part 8**: End-to-End Demo + Wrap-up |

---

## Learning Objectives

By the end of today, you will:
1. Understand pipeline orchestration concepts
2. Run a complete Bronze → Silver → Gold pipeline in Dagster
3. Query data using SQL (basic to advanced)
4. Connect Superset to your Lakehouse
5. Build your first dashboard
6. Understand data quality validation with Soda

---

## Part 1: Dremio Setup & Verification (45 min)

Before running the pipeline, verify Dremio has the required sources configured.

### 1.1 Open Dremio

Open Dremio: **http://localhost:9047** (login: `dremio` / `dremio123`)

### 1.2 Verify Data Sources

You should see two data sources in the left panel:
- **minio** - S3 source pointing to MinIO (for staging data)
- **catalog** - Nessie catalog for Iceberg tables

If they're missing, create them now:

#### Create the MinIO Source

1. Click **"+ Add Data Source"** (or **"Add Source"**)
2. Select **"Amazon S3"**
3. Configure:
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
4. Click **Save**

#### Create the Nessie Catalog Source

1. Click **"+ Add Data Source"**
2. Select **"Nessie"** (or "Arctic")
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
4. Click **Save**

### 1.3 Create the Bronze Folder Structure

In the Nessie catalog, create the bronze folder:

1. Click on **catalog** in the left panel
2. Click the **+** icon or right-click → **New Folder**
3. Create folder: `bronze`

### 1.4 Verify Connection

Run a quick test query in the SQL Editor:

```sql
-- Should return empty (no tables yet)
SHOW TABLES IN catalog.bronze;
```

**You're ready!** The pipeline will create the Iceberg tables automatically.

---

## Part 2: Dagster Orchestration Deep Dive (60 min)

### What is Dagster?

Dagster is a **data orchestrator** that helps you:
- Define data pipelines as code
- Track data lineage (what depends on what)
- Monitor pipeline runs
- Handle failures gracefully

Think of it as the "conductor" of your data orchestra.

### 2.1 Access Dagster

Open your browser and go to: **http://localhost:3000**

You should see the Dagster UI with these menu items:
- **Overview**: Dashboard summary
- **Runs**: History of pipeline executions
- **Catalog**: Your data assets (Bronze, Silver, Gold tables)
- **Jobs**: Pre-defined workflows you can trigger
- **Deployment**: Server status and daemon health

> **Important**: Verify daemon status under **Deployment** - all daemons should show "Running".

### 2.2 Understanding the Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     DAGSTER PIPELINE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────┐     ┌──────────────────┐                    │
│   │bronze_staging│────▶│bronze_iceberg_   │                    │
│   │   (Python)   │     │    tables        │                    │
│   │              │     │   (Dremio CTAS)  │                    │
│   └──────────────┘     └────────┬─────────┘                    │
│                                 │                               │
│                                 ▼                               │
│                        ┌──────────────────┐                    │
│                        │silver_dbt_assets │                    │
│                        │     (dbt run)    │                    │
│                        └────────┬─────────┘                    │
│                                 │                               │
│                                 ▼                               │
│                        ┌──────────────────┐                    │
│                        │ gold_dbt_assets  │                    │
│                        │     (dbt run)    │                    │
│                        └──────────────────┘                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Explore the Assets

1. Click on **"Catalog"** in the left sidebar
2. You'll see four assets in two groups:

**Bronze Group (2 assets):**
   - `bronze_staging` - Uploads raw files to MinIO as Parquet
   - `bronze_iceberg_tables` - Creates Iceberg tables in Nessie catalog

**Silver & Gold (dbt):**
   - `silver_dbt_assets` - dbt Silver transformations
   - `gold_dbt_assets` - dbt Gold aggregations

The arrows show dependencies - data flows from Bronze → Silver → Gold.

### 2.4 Understanding the Code

The pipeline is defined in `orchestration/orchestration/assets.py`:

```python
# Bronze Layer - Stage 1: Upload to MinIO
@asset(group_name="bronze")
def bronze_staging(context):
    # Reads CSV/JSON, writes Parquet to MinIO staging
    ...

# Bronze Layer - Stage 2: Create Iceberg tables
@asset(group_name="bronze", deps=[bronze_staging])
def bronze_iceberg_tables(context):
    # Uses Dremio CTAS to create Iceberg tables
    ...

# Silver Layer - dbt transformations
@dbt_assets(manifest=dbt_silver_manifest_path)
def silver_dbt_assets(context, dbt_silver):
    yield from dbt_silver.cli(["build"], context=context).stream()
```

### 2.5 Jobs: How to Run Pipelines

Jobs are defined in `orchestration/orchestration/definitions.py`:

```python
# Run all Bronze assets
bronze_job = define_asset_job(
    name="bronze_ingestion",
    selection=AssetSelection.groups("bronze"),
)

# Run everything
full_pipeline_job = define_asset_job(
    name="full_lakehouse_pipeline",
    selection=AssetSelection.all(),
)
```

**Available Jobs:**

| Job Name | What it does |
|----------|--------------|
| `bronze_ingestion` | Only ingests raw data to Bronze |
| `silver_transformation` | Only runs Silver dbt models |
| `gold_transformation` | Only runs Gold dbt models |
| `full_lakehouse_pipeline` | Runs all three in sequence |

---

## Part 3: Running the Full Pipeline (60 min)

### 3.1 Run Bronze Ingestion

Let's start with just the Bronze layer:

1. Click **"Jobs"** in the sidebar
2. Click on **"bronze_ingestion"**
3. Click **"Launch Run"** button (top right)
4. Watch the pipeline execute!

**What happens:**
1. `bronze_staging`: Reads 7 CSV/JSONL files, writes Parquet to MinIO
2. `bronze_iceberg_tables`: Creates 7 Iceberg tables via Dremio CTAS

### 3.2 Verify in MinIO

1. Open MinIO: **http://localhost:9001** (login: `minio` / `minioadmin`)
2. Click on **lakehouse** bucket
3. Browse to `staging/` - you should see:
   - `staging/ecoride/customers.parquet`
   - `staging/ecoride/sales.parquet`
   - `staging/chargenet/stations.parquet`
   - etc.

### 3.3 Verify in Dremio

1. Open Dremio: **http://localhost:9047**
2. Click on **catalog** → **bronze**
3. You should see 7 Iceberg tables:
   - `ecoride_customers`
   - `ecoride_sales`
   - `ecoride_vehicles`
   - `ecoride_product_reviews`
   - `chargenet_stations`
   - `chargenet_charging_sessions`
   - `vehicle_health_logs`

### 3.4 Run Full Pipeline

Now run the complete Bronze → Silver → Gold:

1. Click **"Jobs"** → **"full_lakehouse_pipeline"**
2. Click **"Launch Run"**
3. Watch all 4 assets execute in sequence

### 3.5 Monitor Progress

While the pipeline runs:
- Click on individual steps to see logs
- Errors are shown in red with stack traces
- Metadata shows row counts and timing

---

## Part 4: Exploring Results in Dremio (30 min)

Now let's query our Lakehouse data!

### 4.1 Basic Queries (Warmup)

```sql
-- Count customers
SELECT COUNT(*) AS total_customers
FROM catalog.silver.customers;

-- View first 10 customers
SELECT * FROM catalog.silver.customers LIMIT 10;

-- Customers by state
SELECT state, COUNT(*) AS customer_count
FROM catalog.silver.customers
GROUP BY state
ORDER BY customer_count DESC;
```

### 4.2 Aggregations (Intermediate)

```sql
-- Total sales by payment method
SELECT
    payment_method,
    COUNT(*) AS num_sales,
    SUM(sale_price) AS total_revenue,
    AVG(sale_price) AS avg_sale
FROM catalog.silver.sales
GROUP BY payment_method
ORDER BY total_revenue DESC;

-- Monthly sales trend
SELECT
    DATE_TRUNC('month', sale_date) AS month,
    COUNT(*) AS num_sales,
    SUM(sale_price) AS revenue
FROM catalog.silver.sales
GROUP BY DATE_TRUNC('month', sale_date)
ORDER BY month;
```

### 4.3 JOINs (Advanced)

```sql
-- Sales with customer info
SELECT
    s.id AS sale_id,
    c.first_name,
    c.email,
    c.city,
    s.sale_price,
    s.sale_date
FROM catalog.silver.sales s
JOIN catalog.silver.customers c ON s.customer_id = c.id
ORDER BY s.sale_date DESC
LIMIT 20;

-- Top 10 customers by total spend
SELECT
    c.id,
    c.first_name,
    c.email,
    COUNT(s.id) AS num_purchases,
    SUM(s.sale_price) AS total_spent
FROM catalog.silver.customers c
JOIN catalog.silver.sales s ON c.id = s.customer_id
GROUP BY c.id, c.first_name, c.email
ORDER BY total_spent DESC
LIMIT 10;
```

### 4.4 Iceberg Time Travel (Lakehouse Feature!)

```sql
-- Query historical data (see data as it was 1 hour ago)
SELECT * FROM catalog.bronze.ecoride_customers
AT TIMESTAMP AS OF TIMESTAMPADD(HOUR, -1, CURRENT_TIMESTAMP)
LIMIT 10;

-- View table history
SELECT * FROM TABLE(table_history('catalog.bronze.ecoride_customers'));

-- View snapshots
SELECT * FROM TABLE(table_snapshot('catalog.bronze.ecoride_customers'));
```

> 💡 **This is a key Lakehouse feature!** Unlike traditional databases, Iceberg tables keep a full history.

---

## Part 5: Superset Setup & Connection (45 min)

### What is Superset?

Apache Superset is an open-source **Business Intelligence** tool that lets you:
- Connect to various data sources
- Create charts and dashboards
- Share insights with your team

### 5.1 Access Superset

Open your browser: **http://localhost:8088**

Login with:
- Username: `admin`
- Password: `admin`

### 5.2 Connect to Dremio

1. Go to **Settings** (gear icon) → **Database Connections**
2. Click **"+ Database"**
3. Scroll down and select **"Other"**
4. In the SQLAlchemy URI field, paste:

```
dremio+flight://dremio:dremio123@dremio:32010/DREMIO?UseEncryption=false
```

5. Set Display Name to: `Dremio Lakehouse`
6. Click **"Test Connection"** - should show "Connection looks good!"
7. Click **"Connect"**

> **Troubleshooting:** If connection fails, verify:
> - Port is `32010` (Flight protocol), not 9047
> - Host is `dremio` (Docker network name)
> - `UseEncryption=false` is included

### 5.3 Create Your First Dataset

A Dataset in Superset is a table or view you want to visualize.

1. Go to **Data** → **Datasets**
2. Click **"+ Dataset"**
3. Select:
   - Database: `Dremio Lakehouse`
   - Schema: Browse to find `catalog.silver`
   - Table: Select `customers`
4. Click **"Create Dataset and Create Chart"**

---

## Part 6: Building Dashboards (60 min)

### 6.1 Chart 1: Big Number - Total Customers

1. Chart Type: **Big Number**
2. Configure:
   - Metric: `COUNT(*)`
3. Click **"Update Chart"**
4. Click **"Save"** → Name: "Total Customers"
5. Add to new dashboard: "EV Lakehouse Analytics"

### 6.2 Chart 2: Bar Chart - Customers by State

1. Create new chart from `customers` dataset
2. Chart Type: **Bar Chart**
3. Configure:
   - X-Axis: `state`
   - Metrics: `COUNT(*)`
   - Sort: Descending by value
4. Save as "Customers by State"

### 6.3 Chart 3: Line Chart - Monthly Sales Trend

1. Create dataset from `catalog.silver.sales`
2. Chart Type: **Time-series Line Chart**
3. Configure:
   - Time Column: `sale_date`
   - Time Grain: `Month`
   - Metrics: `SUM(sale_price)`, `COUNT(*)`
4. Save as "Monthly Sales Trend"

### 6.4 Chart 4: Pie Chart - Payment Methods

1. Use `sales` dataset
2. Chart Type: **Pie Chart**
3. Configure:
   - Dimensions: `payment_method`
   - Metrics: `COUNT(*)`
4. Save as "Payment Methods"

### 6.5 Chart 5: Table - Top Customers

1. Use custom SQL dataset:
```sql
SELECT
    c.first_name,
    c.email,
    c.state,
    COUNT(s.id) AS purchases,
    SUM(s.sale_price) AS total_spent
FROM catalog.silver.customers c
JOIN catalog.silver.sales s ON c.id = s.customer_id
GROUP BY c.first_name, c.email, c.state
ORDER BY total_spent DESC
LIMIT 20
```
2. Chart Type: **Table**
3. Save as "Top Customers"

### 6.6 Assemble the Dashboard

1. Go to **Dashboards** → "EV Lakehouse Analytics"
2. Click **"Edit Dashboard"**
3. Arrange charts:
```
┌────────────────────────────────────────────────────────────────┐
│ [Total Customers]  [Total Revenue]  [Avg Rating]  [Stations]  │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────────┐  ┌────────────────────────────────┐ │
│  │  Customers by State  │  │   Monthly Sales Trend          │ │
│  │     (Bar Chart)      │  │      (Line Chart)              │ │
│  └──────────────────────┘  └────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────┐  ┌────────────────────────────────┐ │
│  │   Payment Methods    │  │      Top Customers             │ │
│  │     (Pie Chart)      │  │        (Table)                 │ │
│  └──────────────────────┘  └────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```
4. Click **"Save"**

---

## Part 7: Data Quality with Soda (45 min)

### What is Soda?

Soda is a **data quality** tool that validates your data against rules:
- Check for missing values
- Validate uniqueness
- Verify referential integrity
- Detect anomalies

### 7.1 Understanding Soda Checks

Check files are in `soda/checks/`. Example from `soda/checks/demo_checks.yml`:

```yaml
# Freshness check - is data recent?
checks for catalog.silver.customers:
  - freshness(created_at) < 1d:
      name: Customer data is fresh
      warn: when > 12h
      fail: when > 24h

# Uniqueness check - no duplicates?
checks for catalog.silver.sales:
  - duplicate_count(id) = 0:
      name: No duplicate sale IDs

# Referential integrity - valid foreign keys?
checks for catalog.silver.sales:
  - reference check:
      name: All sales reference valid customers
      target column: customer_id
      reference column: catalog.silver.customers.id
```

### 7.2 Run Soda Checks (Demo)

From the Dagster container:

```bash
docker exec dagster soda scan \
  -d lakehouse \
  -c /app/soda/configuration.yml \
  /app/soda/checks/demo_checks.yml
```

Expected output:
```
Scan summary:
8/8 checks PASSED
All is good. No failures. No warnings. No errors.
```

### 7.3 Introducing Bad Data

Let's see what happens with bad data:

1. In Dremio, insert a duplicate record:
```sql
INSERT INTO catalog.bronze.ecoride_customers
VALUES (1, 'Duplicate User', 'bad@email', 'Test City', 'XX', 'Test');
```

2. Run Soda again:
```bash
docker exec dagster soda scan -d lakehouse -c /app/soda/configuration.yml /app/soda/checks/demo_checks.yml
```

3. Watch it **FAIL**:
```
✗ duplicate_count(id) = 0 → FAILED (found 1 duplicate)
```

### 7.4 The Data Quality Feedback Loop

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│  Ingest │────▶│ Transform│────▶│ Validate│
│ (Bronze)│     │ (Silver) │     │  (Soda) │
└─────────┘     └─────────┘     └────┬────┘
                                     │
                              ┌──────▼──────┐
                              │ Pass? → ✓   │
                              │ Fail? → Fix │
                              └─────────────┘
```

This ensures data quality is checked **before** it reaches dashboards!

---

## Part 8: End-to-End Demo (30 min)

Let's demonstrate the complete data flow to wrap up the day!

### 8.1 The Data Journey

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPLETE DATA FLOW                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. RAW FILES      data/ecoride_customers.csv                  │
│        │                                                        │
│        ▼                                                        │
│  2. STAGING        MinIO: lakehouse/staging/ecoride/           │
│        │                                                        │
│        ▼                                                        │
│  3. BRONZE         Iceberg: catalog.bronze.ecoride_customers   │
│        │                                                        │
│        ▼                                                        │
│  4. SILVER         Iceberg: catalog.silver.customers           │
│        │                                                        │
│        ▼                                                        │
│  5. GOLD           Iceberg: catalog.gold.customer_metrics      │
│        │                                                        │
│        ▼                                                        │
│  6. DASHBOARD      Superset: EV Lakehouse Analytics            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Live Demo Walkthrough

**Step 1: Show Raw Data**
- Open `data/ecoride_customers.csv` in text editor
- Note: raw CSV format, potentially messy

**Step 2: Trigger Pipeline**
- Dagster: http://localhost:3000
- Jobs → `full_lakehouse_pipeline` → Launch Run
- Watch Bronze → Silver → Gold execute

**Step 3: Verify in MinIO**
- MinIO: http://localhost:9001
- Browse `lakehouse/staging/ecoride/` - see Parquet files
- Browse `lakehouse/bronze/` - see Iceberg metadata folders

**Step 4: Query in Dremio**
- Dremio: http://localhost:9047
```sql
-- Bronze (raw)
SELECT COUNT(*) FROM catalog.bronze.ecoride_customers;

-- Silver (clean)
SELECT COUNT(*) FROM catalog.silver.customers;

-- Show time travel capability
SELECT * FROM TABLE(table_history('catalog.bronze.ecoride_customers'));
```

**Step 5: View Dashboard**
- Superset: http://localhost:8088
- Open "EV Lakehouse Analytics" dashboard
- See data visualized in real-time!

**Step 6: Run Data Quality**
```bash
docker exec dagster soda scan -d lakehouse -c /app/soda/configuration.yml /app/soda/checks/demo_checks.yml
```

### 8.3 Key Takeaways

| What We Built | Why It Matters |
|---------------|----------------|
| Medallion Architecture | Organized data flow (Bronze→Silver→Gold) |
| Iceberg Tables | Time travel, ACID, schema evolution |
| Dagster Orchestration | Automated, observable, reproducible |
| Superset Dashboards | Self-service analytics |
| Soda Quality Checks | Data trust and validation |

---

## Summary

Today you learned:

| Topic | Tool | What You Did |
|-------|------|--------------|
| Orchestration | Dagster | Ran Bronze->Silver->Gold pipeline |
| Visualization | Superset | Connected to Dremio, built dashboard |
| Integration | All | Demonstrated end-to-end data flow |

## Service URLs

| Service | URL |
|---------|-----|
| Dagster | http://localhost:3000 |
| Superset | http://localhost:8088 |
| Dremio | http://localhost:9047 |
| MinIO | http://localhost:9001 |
| JupyterLab | http://localhost:8888 |

## Key Credentials

| Service | Username | Password |
|---------|----------|----------|
| Superset | admin | admin |
| MinIO | minio | minioadmin |
| Dremio | dremio | dremio123 |

## What's Next?

For further learning:
- Add data quality checks with Soda
- Implement incremental models in dbt
- Add more complex Gold aggregations
- Set up automated scheduling
- Deploy to cloud (AWS, GCP, Azure)

---

**Congratulations on completing the Data Lakehouse Course!**
