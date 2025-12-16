"""
Dagster Definitions for Data Lakehouse Pipeline
================================================

dbt transformation pipeline: Silver → Gold + Soda quality checks

Architecture:
- Bronze: Airbyte syncs source data (run manually via Airbyte UI)
- Silver: dbt transformations (clean/standardize Bronze data)
- Gold: dbt transformations (business aggregations)
- Quality: Soda data quality checks after each transformation layer
"""

from dagster import Definitions, define_asset_job, AssetSelection

from .assets import (
    silver_dbt_assets,
    gold_dbt_assets,
    soda_silver_quality,
    soda_gold_quality,
)
from .constants import dbt_silver, dbt_gold


# =============================================================================
# JOBS - dbt Only (Original - No Quality Checks)
# =============================================================================

# Full dbt pipeline: Bronze → Silver → Gold (without quality checks)
full_dbt_pipeline = define_asset_job(
    name="full_dbt_pipeline",
    description="Transform Bronze → Silver → Gold (dbt only, no quality checks)",
    selection=AssetSelection.assets(silver_dbt_assets, gold_dbt_assets),
)

# Individual layer jobs for demo flexibility
silver_job = define_asset_job(
    name="silver_transformation",
    description="Transform Bronze → Silver (clean & standardize raw data)",
    selection=AssetSelection.assets(silver_dbt_assets),
)

gold_job = define_asset_job(
    name="gold_transformation",
    description="Transform Silver → Gold (aggregate & join for analytics)",
    selection=AssetSelection.assets(gold_dbt_assets),
)


# =============================================================================
# JOBS - With Soda Quality Checks
# =============================================================================

# Full pipeline with quality checks: Silver → Soda → Gold → Soda
full_pipeline_with_quality = define_asset_job(
    name="full_pipeline_with_quality",
    description="Complete pipeline: dbt transformations + Soda quality checks",
    selection=AssetSelection.all(),
)

# Silver + quality check
silver_with_quality = define_asset_job(
    name="silver_with_quality",
    description="Silver transformation + Soda quality validation",
    selection=AssetSelection.assets(silver_dbt_assets, soda_silver_quality),
)

# Gold + quality check
gold_with_quality = define_asset_job(
    name="gold_with_quality",
    description="Gold transformation + Soda quality validation",
    selection=AssetSelection.assets(gold_dbt_assets, soda_gold_quality),
)

# Quality checks only (useful for ad-hoc validation)
quality_checks_only = define_asset_job(
    name="quality_checks_only",
    description="Run Soda quality checks on existing Silver and Gold tables",
    selection=AssetSelection.assets(soda_silver_quality, soda_gold_quality),
)


# =============================================================================
# DAGSTER DEFINITIONS
# =============================================================================

defs = Definitions(
    assets=[
        # dbt transformation assets
        silver_dbt_assets,
        gold_dbt_assets,
        # Soda quality check assets
        soda_silver_quality,
        soda_gold_quality,
    ],
    jobs=[
        # Original jobs (dbt only)
        full_dbt_pipeline,
        silver_job,
        gold_job,
        # Jobs with quality checks
        full_pipeline_with_quality,
        silver_with_quality,
        gold_with_quality,
        quality_checks_only,
    ],
    resources={
        "dbt_silver": dbt_silver,
        "dbt_gold": dbt_gold,
    },
)
