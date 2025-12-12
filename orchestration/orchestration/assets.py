"""
Data Lakehouse Pipeline Assets
==============================
Bronze → Silver → Gold transformation pipeline using Dagster.

Bronze: Ingest raw data and create Iceberg tables in Nessie catalog
Silver: Clean and transform data using dbt
Gold: Business-ready aggregations using dbt
"""

import os
import pandas as pd
import boto3
import requests
from pathlib import Path

from dagster import asset, AssetExecutionContext, MaterializeResult, MetadataValue
from dagster_dbt import DbtCliResource, dbt_assets

from .constants import (
    dbt_silver,
    dbt_gold,
    dbt_silver_manifest_path,
    dbt_gold_manifest_path
)


# =============================================================================
# BRONZE LAYER - Data Ingestion with Iceberg Tables
# =============================================================================

def get_s3_client():
    """Create S3 client for MinIO."""
    return boto3.client(
        's3',
        endpoint_url=os.environ.get('AWS_S3_ENDPOINT', 'http://minio:9000'),
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID', 'minio'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY', 'minioadmin')
    )


def ensure_bucket_exists(s3_client, bucket_name: str):
    """Create bucket if it doesn't exist."""
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except:
        s3_client.create_bucket(Bucket=bucket_name)


def get_dremio_token():
    """Get authentication token from Dremio."""
    dremio_host = os.environ.get('DREMIO_HOST', 'dremio')
    dremio_user = os.environ.get('DREMIO_USER', 'dremio')
    dremio_password = os.environ.get('DREMIO_PASSWORD', 'dremio123')

    response = requests.post(
        f"http://{dremio_host}:9047/apiv2/login",
        json={"userName": dremio_user, "password": dremio_password}
    )
    response.raise_for_status()
    return response.json()["token"]


def execute_dremio_sql(token: str, sql: str, wait: bool = True) -> dict:
    """Execute SQL on Dremio and optionally wait for completion."""
    dremio_host = os.environ.get('DREMIO_HOST', 'dremio')

    # Submit the job
    response = requests.post(
        f"http://{dremio_host}:9047/api/v3/sql",
        headers={
            "Authorization": f"_dremio{token}",
            "Content-Type": "application/json"
        },
        json={"sql": sql}
    )
    response.raise_for_status()
    job_id = response.json()["id"]

    if not wait:
        return {"job_id": job_id, "status": "submitted"}

    # Wait for completion
    import time
    for _ in range(60):  # Max 60 seconds
        time.sleep(1)
        job_response = requests.get(
            f"http://{dremio_host}:9047/api/v3/job/{job_id}",
            headers={"Authorization": f"_dremio{token}"}
        )
        if job_response.status_code == 200:
            job_data = job_response.json()
            state = job_data.get("jobState", "UNKNOWN")
            if state == "COMPLETED":
                return {"job_id": job_id, "status": "completed", "rows": job_data.get("rowCount", 0)}
            elif state == "FAILED":
                return {"job_id": job_id, "status": "failed", "error": job_data.get("errorMessage", "Unknown error")}

    return {"job_id": job_id, "status": "timeout"}


def get_file_schema_table(filename: str) -> tuple[str, str]:
    """Map filename to schema and table name."""
    filename_lower = filename.lower()

    if 'chargenet' in filename_lower:
        schema = 'chargenet'
        table = filename_lower.replace('chargenet_', '').split('.')[0]
    elif 'ecoride' in filename_lower:
        schema = 'ecoride'
        table = filename_lower.replace('ecoride_', '').split('.')[0]
    elif 'vehicle_health' in filename_lower:
        schema = 'vehicle_health'
        table = 'logs'
    else:
        return None, None

    return schema, table


@asset(
    group_name="bronze",
    description="Stage 1: Ingest raw data files to MinIO staging area",
    compute_kind="python",
)
def bronze_staging(context: AssetExecutionContext) -> MaterializeResult:
    """
    Bronze Staging: Upload raw data to MinIO as Parquet files.

    This is the first step - getting data into object storage.
    The next step (bronze_iceberg_tables) converts these to Iceberg tables.
    """
    data_folder = os.environ.get('DATA_FOLDER', '/data')
    bucket_name = 'lakehouse'
    staging_path = 'staging'

    # Initialize S3 client
    s3_client = get_s3_client()
    ensure_bucket_exists(s3_client, bucket_name)

    storage_options = {
        'key': os.environ.get('AWS_ACCESS_KEY_ID', 'minio'),
        'secret': os.environ.get('AWS_SECRET_ACCESS_KEY', 'minioadmin'),
        'client_kwargs': {
            'endpoint_url': os.environ.get('AWS_S3_ENDPOINT', 'http://minio:9000')
        }
    }

    files_processed = []
    total_rows = 0

    context.log.info(f"Starting Bronze staging from {data_folder}")

    for filename in os.listdir(data_folder):
        filepath = os.path.join(data_folder, filename)

        if not os.path.isfile(filepath):
            continue

        schema, table = get_file_schema_table(filename)
        if not schema:
            context.log.warning(f"Skipping unmapped file: {filename}")
            continue

        try:
            # Read based on file type
            if filename.endswith('.csv'):
                df = pd.read_csv(filepath)
            elif filename.endswith('.json'):
                df = pd.read_json(filepath)
            elif filename.endswith('.jsonl'):
                df = pd.read_json(filepath, lines=True)
            else:
                continue

            # Write to MinIO staging area
            s3_path = f"s3a://{bucket_name}/{staging_path}/{schema}/{table}.parquet"
            df.to_parquet(s3_path, engine='pyarrow', index=False, storage_options=storage_options)

            files_processed.append(f"{schema}.{table}")
            total_rows += len(df)
            context.log.info(f"Staged {filename} → {staging_path}/{schema}/{table}.parquet ({len(df)} rows)")

        except Exception as e:
            context.log.error(f"Failed to process {filename}: {e}")

    return MaterializeResult(
        metadata={
            "files_processed": MetadataValue.int(len(files_processed)),
            "total_rows": MetadataValue.int(total_rows),
            "tables": MetadataValue.json(files_processed),
        }
    )


@asset(
    group_name="bronze",
    description="Create Iceberg tables directly in Nessie catalog",
    compute_kind="dremio",
    deps=[bronze_staging],
)
def bronze_iceberg_tables(context: AssetExecutionContext) -> MaterializeResult:
    """
    Bronze Iceberg Tables: Create proper Iceberg tables in Nessie catalog.

    Reads data from MinIO staging and creates Iceberg tables via Dremio.
    Uses CREATE TABLE + INSERT for proper Iceberg table creation.
    """
    # Table definitions: (domain, table_name)
    tables = [
        ('ecoride', 'customers'),
        ('ecoride', 'sales'),
        ('ecoride', 'vehicles'),
        ('ecoride', 'product_reviews'),
        ('chargenet', 'stations'),
        ('chargenet', 'charging_sessions'),
        ('vehicle_health', 'logs'),
    ]

    try:
        token = get_dremio_token()
        context.log.info("Connected to Dremio")
    except Exception as e:
        context.log.error(f"Failed to connect to Dremio: {e}")
        return MaterializeResult(
            metadata={"error": MetadataValue.text(str(e))}
        )

    # Storage options for reading from MinIO
    storage_options = {
        'key': os.environ.get('AWS_ACCESS_KEY_ID', 'minio'),
        'secret': os.environ.get('AWS_SECRET_ACCESS_KEY', 'minioadmin'),
        'client_kwargs': {'endpoint_url': os.environ.get('AWS_S3_ENDPOINT', 'http://minio:9000')}
    }

    tables_created = []
    tables_failed = []

    for domain, table in tables:
        iceberg_table = f"catalog.bronze.{domain}_{table}"
        staging_path = f"lakehouse/staging/{domain}/{table}.parquet"

        context.log.info(f"Creating Iceberg table: {iceberg_table}")

        try:
            # Read the parquet file to get schema and data
            df = pd.read_parquet(f"s3://{staging_path}", storage_options=storage_options)

            # Drop existing table
            execute_dremio_sql(token, f'DROP TABLE IF EXISTS {iceberg_table}')

            # Build CREATE TABLE statement with schema
            columns = []
            for col_name, dtype in df.dtypes.items():
                if 'int' in str(dtype):
                    sql_type = 'BIGINT'
                elif 'float' in str(dtype):
                    sql_type = 'DOUBLE'
                elif 'datetime' in str(dtype) or 'date' in str(dtype).lower():
                    sql_type = 'TIMESTAMP'
                else:
                    # Use large VARCHAR for text fields to accommodate long content
                    sql_type = 'VARCHAR(65535)'
                columns.append(f'"{col_name}" {sql_type}')

            create_sql = f'CREATE TABLE {iceberg_table} ({", ".join(columns)})'
            result = execute_dremio_sql(token, create_sql)

            if result["status"] != "completed":
                raise Exception(f"CREATE TABLE failed: {result.get('error', result['status'])}")

            # Insert data in batches
            batch_size = 500
            total_inserted = 0

            def format_value(val, dtype):
                """Format a value for SQL INSERT."""
                import json
                if pd.isna(val):
                    return 'NULL'
                elif 'datetime' in str(dtype):
                    # Format timestamp
                    return f"TIMESTAMP '{val}'"
                elif isinstance(val, (list, dict)):
                    # Convert complex types to JSON string
                    json_str = json.dumps(val).replace("'", "''")
                    return f"'{json_str}'"
                elif isinstance(val, str):
                    # First convert Unicode quotes to ASCII, then escape
                    normalized = (val
                        .replace("'", "'")       # Unicode right single quote -> ASCII
                        .replace("'", "'")       # Unicode left single quote -> ASCII
                        .replace('"', '"')       # Unicode left double quote -> ASCII
                        .replace('"', '"'))      # Unicode right double quote -> ASCII
                    # Now escape and clean
                    escaped = (normalized
                        .replace("'", "''")      # Escape ASCII apostrophe
                        .replace('\n', ' ')
                        .replace('\r', '')
                        .replace('\t', ' '))
                    return f"'{escaped}'"
                elif isinstance(val, bool):
                    return 'TRUE' if val else 'FALSE'
                else:
                    return str(val)

            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i+batch_size]
                values = []
                for _, row in batch.iterrows():
                    row_values = []
                    for col_idx, val in enumerate(row.values):
                        dtype = df.dtypes.iloc[col_idx]
                        row_values.append(format_value(val, dtype))
                    values.append(f"({', '.join(row_values)})")

                if values:
                    insert_sql = f'INSERT INTO {iceberg_table} VALUES {", ".join(values)}'
                    result = execute_dremio_sql(token, insert_sql)
                    if result["status"] == "completed":
                        total_inserted += len(batch)
                    else:
                        context.log.warning(f"INSERT batch {i//batch_size}: status={result['status']}, error={result.get('error', 'N/A')[:300]}")

            tables_created.append(iceberg_table)
            context.log.info(f"✓ Created {iceberg_table} ({total_inserted} rows)")

        except Exception as e:
            tables_failed.append(f"{iceberg_table}: {str(e)}")
            context.log.error(f"✗ Failed to create {iceberg_table}: {e}")

    return MaterializeResult(
        metadata={
            "tables_created": MetadataValue.int(len(tables_created)),
            "tables_failed": MetadataValue.int(len(tables_failed)),
            "created": MetadataValue.json(tables_created),
            "failed": MetadataValue.json(tables_failed),
        }
    )


# =============================================================================
# SILVER LAYER - dbt Transformations
# =============================================================================

@dbt_assets(
    manifest=dbt_silver_manifest_path,
    select="fqn:*",
    name="silver_dbt_assets",
)
def silver_dbt_assets(context: AssetExecutionContext, dbt_silver: DbtCliResource):
    """
    Silver Layer: Clean and standardize data using dbt.

    Transforms raw Bronze Iceberg tables into clean, typed, deduplicated tables.
    """
    yield from dbt_silver.cli(["build"], context=context).stream()


# =============================================================================
# GOLD LAYER - dbt Aggregations
# =============================================================================

@dbt_assets(
    manifest=dbt_gold_manifest_path,
    select="fqn:*",
    name="gold_dbt_assets",
)
def gold_dbt_assets(context: AssetExecutionContext, dbt_gold: DbtCliResource):
    """
    Gold Layer: Business-ready aggregations using dbt.

    Creates analytics-ready tables like customer lifetime value,
    vehicle utilization metrics, and charging station performance.
    """
    yield from dbt_gold.cli(["build"], context=context).stream()
