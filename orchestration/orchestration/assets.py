"""
Data Lakehouse Pipeline Assets
==============================
Silver → Gold transformation pipeline using Dagster + dbt + Soda.

Architecture:
- Bronze: Airbyte syncs source data (run manually via Airbyte UI)
- Silver: dbt transformations (clean/standardize Bronze data)
- Gold: dbt transformations (business aggregations)
- Quality: Soda data quality checks after each layer
"""

import subprocess
from dagster import asset, AssetExecutionContext, Output, MetadataValue
from dagster_dbt import DbtCliResource, dbt_assets

from .constants import (
    dbt_silver_manifest_path,
    dbt_gold_manifest_path,
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


# =============================================================================
# SODA DATA QUALITY CHECKS
# =============================================================================

def _run_soda_scan(context, config_file: str, checks_file: str, layer_name: str) -> dict:
    """
    Helper function to run Soda scans and parse results.

    Returns dict with check results and metadata.
    """
    context.log.info(f"Running Soda {layer_name} quality checks...")

    result = subprocess.run(
        [
            "soda", "scan",
            "-d", "lakehouse",
            "-c", config_file,
            checks_file
        ],
        capture_output=True,
        text=True
    )

    # Log the full output
    context.log.info(f"Soda output:\n{result.stdout}")
    if result.stderr:
        context.log.warning(f"Soda stderr:\n{result.stderr}")

    # Parse results from output
    passed = failed = warnings = errors = 0
    for line in result.stdout.split('\n'):
        if 'checks PASSED' in line:
            # Extract number like "23/23 checks PASSED"
            parts = line.split('/')
            if len(parts) >= 2:
                passed = int(parts[0].split()[-1])
        elif 'FAILED' in line and 'checks' in line.lower():
            parts = line.split()
            for i, p in enumerate(parts):
                if p.isdigit():
                    failed = int(p)
                    break

    return {
        "passed": passed,
        "failed": failed,
        "return_code": result.returncode,
        "output": result.stdout,
    }


@asset(
    deps=[silver_dbt_assets],
    group_name="quality",
    description="Soda data quality checks for Silver layer",
)
def soda_silver_quality(context: AssetExecutionContext):
    """
    Run Soda data quality checks on Silver layer tables.

    Validates:
    - Row counts (tables have data)
    - No duplicate primary keys
    - No missing required fields
    - Valid email formats
    - No negative values where inappropriate
    """
    results = _run_soda_scan(
        context,
        config_file="/app/soda/configuration_silver.yml",
        checks_file="/app/soda/checks/silver_checks.yml",
        layer_name="Silver"
    )

    if results["return_code"] != 0:
        raise Exception(
            f"Soda Silver quality checks failed!\n"
            f"Passed: {results['passed']}, Failed: {results['failed']}\n"
            f"Output:\n{results['output']}"
        )

    return Output(
        value=results,
        metadata={
            "checks_passed": MetadataValue.int(results["passed"]),
            "checks_failed": MetadataValue.int(results["failed"]),
            "soda_output": MetadataValue.md(f"```\n{results['output']}\n```"),
        }
    )


@asset(
    deps=[gold_dbt_assets],
    group_name="quality",
    description="Soda data quality checks for Gold layer",
)
def soda_gold_quality(context: AssetExecutionContext):
    """
    Run Soda data quality checks on Gold layer tables.

    Validates:
    - Aggregation tables have data
    - No duplicate keys in denormalized tables
    - Business metrics are within expected ranges
    - Valid categorical values
    """
    results = _run_soda_scan(
        context,
        config_file="/app/soda/configuration_gold.yml",
        checks_file="/app/soda/checks/gold_checks.yml",
        layer_name="Gold"
    )

    if results["return_code"] != 0:
        raise Exception(
            f"Soda Gold quality checks failed!\n"
            f"Passed: {results['passed']}, Failed: {results['failed']}\n"
            f"Output:\n{results['output']}"
        )

    return Output(
        value=results,
        metadata={
            "checks_passed": MetadataValue.int(results["passed"]),
            "checks_failed": MetadataValue.int(results["failed"]),
            "soda_output": MetadataValue.md(f"```\n{results['output']}\n```"),
        }
    )
