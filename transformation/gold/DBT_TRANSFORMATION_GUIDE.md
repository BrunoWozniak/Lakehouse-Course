# dbt Gold Layer - Business-Ready Data

This dbt project transforms cleaned data from the **silver layer** into business-ready, analytics-optimized data in the **gold layer**.

## What is the Gold Layer?

The gold layer contains:
- Aggregated metrics and KPIs
- Denormalized tables optimized for reporting
- Business logic and derived fields
- Data ready for dashboards and analytics tools

## Architecture

```
Silver (Cleaned Data)       Gold (Business-Ready)
─────────────────────       ─────────────────────
Dremio Silver        →      Dremio Gold
(Structured tables)   dbt   (Analytics tables)
```

## Project Structure

```
transformation/gold/
├── dbt_project.yml      # Project configuration
├── profiles.yml         # Connection settings (Dremio)
├── models/
│   ├── sources.yml      # Define silver layer sources
│   └── ecoride/         # EcoRide business models
│       ├── customers_gold.sql        # Enriched customer data
│       ├── customer_lifetime_value.sql
│       ├── customer_segmentation.sql
│       ├── enriched_sales.sql
│       └── vehicle_usage.sql
├── seeds/               # Static reference data
├── tests/               # Custom data tests
└── macros/              # Reusable SQL snippets
```

## Key Files Explained

| File | Purpose |
|------|---------|
| `dbt_project.yml` | Project name, paths, materialization settings |
| `profiles.yml` | Dremio connection (writes to gold folder) |
| `models/sources.yml` | Maps silver layer tables as sources |
| `models/*.sql` | Business transformation logic |

## The Customers Gold Model

**Location:** `models/ecoride/customers_gold.sql`

This model creates an enriched customer table for analytics:

```sql
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
- Reads from: `catalog.silver.customers`
- Writes to: `lakehouse.gold.customers_gold`
- Adds derived fields (`country_code`, `location`)
- Renames `id` to `customer_id` for clarity
- Creates an analytics-ready table

**Data flow:**
```
Bronze → Silver → Gold
(raw)    (clean)  (business-ready)
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

3. Ensure silver layer data exists (run silver transformations first)

### Commands

From the `transformation/gold` directory:

| Command | Description |
|---------|-------------|
| `dbt run` | Run all gold models |
| `dbt run --select customers_gold` | Run only the customers_gold model |
| `dbt run --select ecoride.*` | Run all ecoride models |
| `dbt test` | Run data quality tests |
| `dbt compile` | Compile SQL without running |

### Quick Start

```bash
cd transformation/gold
source ../../.venv/bin/activate
export DREMIO_USER=dremio
export DREMIO_PASSWORD=dremio123

# Transform customers from silver to gold
dbt run --select customers_gold
```

### Expected Output

```
Running with dbt=1.10.15
Found 7 models, 7 sources
1 of 1 START sql table model catalog.gold.customers_gold
1 of 1 OK created sql table model catalog.gold.customers_gold [12500 in 1.30s]
Completed successfully
```

## Full Pipeline: Bronze → Silver → Gold

Run the complete transformation pipeline:

```bash
# 1. Transform bronze to silver
cd transformation/silver
source ../../.venv/bin/activate
export DREMIO_USER=dremio
export DREMIO_PASSWORD=dremio123
dbt run --select customers

# 2. Transform silver to gold
cd ../gold
dbt run --select customers_gold
```

## Querying the Results

After running dbt, query the gold layer in Dremio:

```sql
-- Basic query
SELECT * FROM lakehouse.gold.customers_gold LIMIT 10;

-- Customers by country
SELECT country_code, COUNT(*) as customer_count
FROM lakehouse.gold.customers_gold
GROUP BY country_code
ORDER BY customer_count DESC;

-- Customers by location
SELECT location, COUNT(*) as customers
FROM lakehouse.gold.customers_gold
GROUP BY location;
```

## Other Gold Models

| Model | Description |
|-------|-------------|
| `customer_lifetime_value` | Total spent, transaction count, average value per customer |
| `customer_segmentation` | Customer profiles with purchase patterns and preferred models |
| `enriched_sales` | Sales data joined with customer and vehicle details |
| `vehicle_usage` | Vehicle usage patterns and statistics |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `Source silver.customers not found` | Run silver transformations first |
| `DREMIO_USER not provided` | Set environment variables |
| `Unauthorized (401)` | Check Dremio username/password |

## Adding New Gold Models

1. Create a new `.sql` file in `models/ecoride/`
2. Reference silver sources with `{{ source('silver', 'table_name') }}`
3. Add business logic, aggregations, or derived fields
4. Run `dbt run --select your_model`

Example pattern for a new gold model:
```sql
{{ config(materialized="table", twin_strategy="allow") }}

SELECT
    -- Include key identifiers
    -- Add aggregations
    -- Create derived fields
FROM {{ source('silver', 'source_table') }}
-- JOIN other sources as needed
-- GROUP BY for aggregations
```
