from setuptools import find_packages, setup

setup(
    name="orchestration",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        # Dagster core
        "dagster",
        "dagster-webserver",
        "dagster-dbt",
        # dbt for Dremio
        "dbt-core",
        "dbt-dremio",
        # Bronze layer dependencies
        "pandas",
        "boto3",
        "pyarrow",
        "s3fs",
        "requests",
        # Data quality
        "soda-core-dremio",
    ],
)