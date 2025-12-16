# Data Lakehouse Course

A hands-on training course on building a modern Data Lakehouse using 100% open-source technologies.

## Business Scenario

You are a **Data Engineer at an EV (Electric Vehicle) company**. Your company has three data domains:

| Domain | Description | Data |
|--------|-------------|------|
| **EcoRide** | Vehicle sales and customer data | customers, sales, vehicles, product_reviews |
| **ChargeNet** | EV charging infrastructure | stations, charging_sessions |
| **VehicleHealth** | Fleet maintenance and diagnostics | vehicle_health_logs |

Your mission: Build a unified analytics platform using the **Medallion Architecture** (Bronze -> Silver -> Gold).

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA LAKEHOUSE ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│   │  SOURCE  │    │  BRONZE  │    │  SILVER  │    │   GOLD   │             │
│   │  FILES   │───▶│  Iceberg │───▶│  Iceberg │───▶│  Iceberg │             │
│   │ CSV/JSON │    │  Tables  │    │  Tables  │    │  Tables  │             │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘             │
│        │               │               │               │                    │
│     Airbyte           dbt             dbt           Superset                │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │              MinIO (S3) + Nessie (Catalog) + Dremio (SQL)        │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                    │                                        │
│              ┌─────────────────────┴─────────────────────┐                 │
│              ▼                                           ▼                  │
│        ┌──────────┐                               ┌──────────┐             │
│        │  Dagster │                               │   Soda   │             │
│        │(Orchestr)│                               │(Quality) │             │
│        └──────────┘                               └──────────┘             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Technology Stack

| Component | Technology | Port | Purpose |
|-----------|------------|------|---------|
| Object Storage | MinIO | 9000, 9001 | S3-compatible storage for data files |
| Query Engine | Dremio | 9047, 31010, 32010 | SQL queries on lakehouse data |
| Catalog | Nessie | 19120 | Iceberg table versioning and metadata |
| Data Ingestion | Airbyte | 8000 | Extract & Load to Bronze (via abctl) |
| Transformations | dbt | - | SQL-based data transformations |
| Orchestration | Dagster | 3000 | Pipeline scheduling and monitoring |
| Data Quality | Soda | - | Data validation and quality checks |
| Visualization | Superset | 8088 | BI dashboards and charts |
| Notebooks | JupyterLab | 8888 | Interactive data exploration |
| **AI Agent** | **LangChain + Mistral** | **8501** | **Natural language SQL queries (NEW!)** |

## Quick Start

### 1. Start All Services

```bash
docker compose up -d
```

### 2. Install Airbyte (separate from docker-compose)

```bash
curl -LsfS https://get.airbyte.com | bash -
abctl local install
abctl local credentials  # Get login credentials
```

### 3. Access the Services

| Service | URL | Credentials |
|---------|-----|-------------|
| Dremio | http://localhost:9047 | dremio / dremio123 |
| MinIO Console | http://localhost:9001 | minio / minioadmin |
| Airbyte | http://localhost:8000 | See `abctl local credentials` |
| Dagster | http://localhost:3000 | No auth required |
| Superset | http://localhost:8088 | admin / admin |
| JupyterLab | http://localhost:8888 | No token required |

### 4. Run the Pipeline

1. Configure Airbyte sources and sync to Bronze
2. Open Dagster at http://localhost:3000
3. Run the `full_pipeline_with_quality` job (dbt + Soda)

## Project Structure

```
lakehouse/
├── data/                      # Raw data files (CSV, JSON, JSONL)
├── transformation/
│   ├── silver/                # dbt project for Silver layer
│   └── gold/                  # dbt project for Gold layer
├── orchestration/             # Dagster pipeline definitions
├── soda/                      # Soda data quality checks
│   ├── configuration_silver.yml
│   ├── configuration_gold.yml
│   └── checks/
├── docker/
│   ├── dagster/               # Dagster Dockerfile (includes dbt + Soda)
│   └── superset/              # Superset Dockerfile with Dremio driver
├── docker-compose.yml         # Service orchestration
├── LAKEHOUSE_FROM_SCRATCH.md  # Comprehensive setup guide
└── README.md                  # This file
```

## Data Files

The `data/` folder contains:

| File | Format | Records | Description |
|------|--------|---------|-------------|
| ecoride_customers.csv | CSV | ~2,500 | Customer information |
| ecoride_sales.csv | CSV | ~5,800 | Vehicle sales transactions |
| ecoride_vehicles.csv | CSV | ~40 | Vehicle catalog |
| ecoride_product_reviews.jsonl | JSONL | ~50 | Customer reviews |
| chargenet_stations.jsonl | JSONL | ~250 | Charging station locations |
| chargenet_charging_sessions.jsonl | JSONL | ~12,000 | Charging session logs |
| vehicle_health_data.jsonl | JSONL | ~3,200 | Vehicle diagnostics |

## Documentation

For the complete step-by-step guide, see **[LAKEHOUSE_FROM_SCRATCH.md](LAKEHOUSE_FROM_SCRATCH.md)**.

This comprehensive guide covers:
- Infrastructure setup
- Dremio-Nessie-MinIO integration
- Airbyte data ingestion
- dbt transformations (Silver & Gold)
- Soda data quality checks
- Dagster orchestration
- Superset visualization

## Superset Connection

To connect Superset to Dremio:

```
dremio+flight://dremio:dremio123@dremio:32010/dremio?UseEncryption=false
```

## AI Agent - Natural Language SQL Queries (NEW!)

Ask questions in plain English and get SQL-powered answers from your Data Lakehouse!

### Features
- Natural language to SQL conversion
- Powered by Mistral AI (100% FREE tier)
- Interactive chat interface with Chainlit
- Query all Gold layer tables
- See the generated SQL queries
- Perfect for learning LangChain and AI agents

### Quick Setup (5 minutes)

1. Get a free Mistral API key at https://console.mistral.ai/
2. Configure the agent:
   ```bash
   cd agent
   cp .env.example .env
   # Edit .env and add your Mistral API key
   ```
3. Start the agent:
   ```bash
   docker-compose up -d lakehouse-agent
   ```
4. Open http://localhost:8501

### Example Questions
- "What is the total customer lifetime value?"
- "Which charging stations have the highest utilization?"
- "Show me the top 5 customers by revenue"
- "What are the most common vehicle health issues?"

### Documentation
- Quick Start: `agent/QUICKSTART.md`
- Getting Started: `agent/GETTING_STARTED.md`
- Full Documentation: `agent/README.md`
- Architecture Details: `agent/ARCHITECTURE.md`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Dremio not showing tables | Ensure Airbyte sync completed, refresh metadata |
| Superset connection fails | Use port 32010 (Flight), include `?UseEncryption=false` |
| Dagster dbt errors | Check Dremio is running, verify credentials in profiles.yml |
| Soda "Can't open lib" | Rebuild Dagster container to install ODBC driver |
| Agent API key error | Create `.env` file in `agent/` with your Mistral API key |
| Agent can't connect to Dremio | Ensure Dremio is running, check `docker ps` |

## License

This course material is provided for educational purposes.
