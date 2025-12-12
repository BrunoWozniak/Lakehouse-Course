"""
Dagster Definitions for Data Lakehouse Pipeline
================================================

This module defines the complete Bronze → Silver → Gold pipeline
with manual job triggers for the course demo.

Bronze Layer has 2 stages:
1. bronze_staging: Upload raw files to MinIO as Parquet
2. bronze_iceberg_tables: Create Iceberg tables in Nessie catalog
"""

from dagster import Definitions, define_asset_job, AssetSelection

from .assets import bronze_staging, bronze_iceberg_tables, silver_dbt_assets, gold_dbt_assets
from .constants import dbt_silver, dbt_gold


# =============================================================================
# JOBS - Manual Triggers for Course Demo
# =============================================================================

# Full pipeline: Bronze → Silver → Gold
full_pipeline_job = define_asset_job(
    name="full_lakehouse_pipeline",
    description="Run complete Bronze → Silver → Gold pipeline",
    selection=AssetSelection.all(),
)

# Individual layer jobs for demo flexibility
bronze_job = define_asset_job(
    name="bronze_ingestion",
    description="Ingest raw data to Bronze layer (staging + Iceberg tables)",
    selection=AssetSelection.groups("bronze"),
)

silver_job = define_asset_job(
    name="silver_transformation",
    description="Run Silver layer dbt transformations",
    selection=AssetSelection.assets(silver_dbt_assets),
)

gold_job = define_asset_job(
    name="gold_transformation",
    description="Run Gold layer dbt transformations",
    selection=AssetSelection.assets(gold_dbt_assets),
)


# =============================================================================
# DAGSTER DEFINITIONS
# =============================================================================

defs = Definitions(
    assets=[
        bronze_staging,
        bronze_iceberg_tables,
        silver_dbt_assets,
        gold_dbt_assets,
    ],
    jobs=[
        full_pipeline_job,
        bronze_job,
        silver_job,
        gold_job,
    ],
    resources={
        "dbt_silver": dbt_silver,
        "dbt_gold": dbt_gold,
    },
)
