# Superset & Orchestration Quick Guide

## Superset (Already Running!)

Superset is running at http://localhost:8088

### Default Login
- Username: `admin`
- Password: `admin`

### Quick Demo for Course

1. **Connect to Dremio**:
   - Settings → Database Connections → + Database
   - Choose "Other"
   - SQLAlchemy URI: `dremio+flight://dremio:dremio123@host.docker.internal:31010/dremio`

   If Flight doesn't work, try:
   - `dremio://dremio:dremio123@host.docker.internal:9047/dremio`

2. **Create a Simple Chart**:
   - Charts → + Chart
   - Choose dataset (once Dremio is connected)
   - Pick chart type (Bar, Line, etc.)
   - Save to dashboard

3. **What to Show Students**:
   - Even without full data, show the Superset UI
   - Explain how it connects to query engines
   - Show chart types available
   - Discuss self-service analytics

## Orchestration Options (Not Installed Yet)

### Option 1: Quick Airflow Setup (If Time)
```bash
# Quick install with pip
pip install apache-airflow==2.7.3

# Initialize database
airflow db init

# Create admin user
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com

# Start webserver (in one terminal)
airflow webserver --port 8080

# Start scheduler (in another terminal)
airflow scheduler
```

### Option 2: Dagster (Easier for Demo)
```bash
# Install
pip install dagster dagster-webserver

# Create simple pipeline file (already provided)
# Start UI
dagster dev -f dagster_pipeline.py

# Open http://localhost:3000
```

### Option 3: Just Explain Orchestration

If no time to install, explain on whiteboard:

"Orchestration tools like Airflow and Dagster schedule and monitor our data pipelines:
1. Trigger Airbyte syncs on schedule
2. Run dbt transformations after ingestion
3. Refresh dashboards after transformations
4. Alert on failures"

Draw a simple DAG:
```
Airbyte Sync → dbt Silver → dbt Gold → Refresh Dashboard
     ↓             ↓            ↓              ↓
   Success?    Success?     Success?      Notify Team
```

## What to Tell Students

### About Superset:
"Superset is our business intelligence tool. It connects to Dremio (or any SQL engine) and lets business users create their own dashboards without coding."

### About Orchestration:
"In production, everything runs on schedules:
- Daily customer data syncs at 2 AM
- Hourly sales updates
- Real-time streaming for critical metrics

Tools like Airflow ensure:
- Dependencies are respected
- Failures are retried
- Teams are notified
- SLAs are met"

## If Students Ask Why Not Installed

"I focused on the core lakehouse components for today. Orchestration is typically added once your pipelines are stable. We'll discuss the concepts and you can install Airflow or Dagster as homework."

## Quick Win

Even without orchestration installed, you can show:
1. Superset UI (it's running!)
2. Explain cron schedules
3. Draw DAG on whiteboard
4. Discuss real-world pipeline scheduling
5. Show them Airflow/Dagster websites