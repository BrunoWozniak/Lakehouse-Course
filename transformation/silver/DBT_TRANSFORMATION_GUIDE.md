# dbt Silver Layer - Data Transformation

This dbt project transforms raw data from the **bronze layer** (MinIO/Iceberg) into cleaned, structured data in the **silver layer** using Dremio as the query engine.

## What is dbt?

dbt (data build tool) is a transformation framework that lets you write SQL SELECT statements to transform your data. It handles:
- Dependency management between models
- Data quality testing
- Documentation generation
- Incremental builds

## Architecture

```
Bronze (Raw Data)          Silver (Cleaned Data)
─────────────────          ───────────────────────
MinIO/Iceberg       →      Dremio Lakehouse
(Airbyte ingested)   dbt   (Queryable tables)
```

## Project Structure

```
transformation/silver/
├── dbt_project.yml      # Project configuration
├── profiles.yml         # Connection settings (Dremio)
├── models/
│   ├── sources.yml      # Define bronze layer sources
│   ├── schema.yml       # Model documentation & tests
│   ├── ecoride/         # EcoRide domain models
│   │   ├── customers.sql
│   │   ├── vehicles.sql
│   │   ├── sales.sql
│   │   └── product_reviews.sql
│   ├── chargenet/       # ChargeNet domain models
│   │   ├── stations.sql
│   │   └── charging_sessions.sql
│   └── vehicle_health/  # Vehicle Health domain models
│       └── vehicle_health_logs.sql
├── seeds/               # Static CSV data (if needed)
├── tests/               # Custom data tests
├── macros/              # Reusable SQL snippets
└── target/              # Compiled SQL (auto-generated)
```

## Key Files Explained

| File | Purpose |
|------|---------|
| `dbt_project.yml` | Project name, paths, materialization settings |
| `profiles.yml` | Dremio connection (host, port, credentials) |
| `models/sources.yml` | Maps bronze layer tables as dbt sources |
| `models/schema.yml` | Column descriptions and data quality tests |
| `models/*.sql` | Transformation logic (SELECT statements) |

## The Customers Model

**Location:** `models/ecoride/customers.sql`

This model transforms raw customer data from bronze to silver:

```sql
SELECT
    id,
    first_name,
    email,
    city,
    "state",
    country
FROM {{ source("ecoride_bronze", "customers") }}
```

**What it does:**
- Reads from: `minio.lakehouse.bronze.ecoride.customers`
- Writes to: `lakehouse.silver.customers`
- Selects only the columns needed for analytics
- Creates a clean, queryable table in Dremio

**Data flow:**
```
PostgreSQL → Airbyte → MinIO (Bronze) → dbt → Dremio (Silver)
```

## Running dbt

### Prerequisites

1. Activate the virtual environment:
   ```bash
   source ../../.venv/bin/activate
   ```

2. Set Dremio credentials:
   ```bash
   export DREMIO_USER=dremio
   export DREMIO_PASSWORD=dremio123
   ```

### Commands

From the `transformation/silver` directory:

| Command | Description |
|---------|-------------|
| `dbt run` | Run all models |
| `dbt run --select customers` | Run only the customers model |
| `dbt run --select ecoride.*` | Run all ecoride models |
| `dbt test` | Run data quality tests |
| `dbt test --select customers` | Test only customers model |
| `dbt compile` | Compile SQL without running |
| `dbt docs generate` | Generate documentation |

### Quick Start

```bash
cd transformation/silver
source ../../.venv/bin/activate
export DREMIO_USER=dremio
export DREMIO_PASSWORD=dremio123

# Transform customers data
dbt run --select customers
```

### Expected Output

```
Running with dbt=1.10.15
Found 8 models, 19 data tests, 7 sources
1 of 1 START sql table model catalog.silver.customers
1 of 1 OK created sql table model catalog.silver.customers [12500 in 2.22s]
Completed successfully
```

## Querying the Results

After running dbt, query the silver layer in Dremio:

```sql
SELECT * FROM lakehouse.silver.customers LIMIT 10;
```

Or connect via JDBC/ODBC tools like Superset at `localhost:9047`.

## Data Quality Tests

The `schema.yml` file defines tests for the customers model:

- `id`: Must be unique and not null
- `first_name`: Documented column
- `email`: Documented column

Run tests with:
```bash
dbt test --select customers
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `DREMIO_USER not provided` | Set environment variables (see above) |
| `Unauthorized (401)` | Check Dremio username/password |
| `Source not found` | Verify bronze data exists in MinIO |
| `dbt: command not found` | Activate the virtual environment |

## Adding New Models

1. Create a new `.sql` file in the appropriate `models/` subdirectory
2. Write a SELECT statement using `{{ source() }}` or `{{ ref() }}`
3. Add documentation in `schema.yml`
4. Run `dbt run --select your_model`
