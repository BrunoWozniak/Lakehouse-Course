-- Silver layer: Vehicle health logs cleaned and standardized
-- Excludes Airbyte metadata columns (_airbyte_*)
-- NOTE: Column names depend on original JSON field names - may need adjustment

{{ config(materialized="table", twin_strategy="allow") }}

SELECT
    VehicleID AS vehicle_id,
    Model AS model,
    ManufacturingYear AS manufacturing_year,
    Alerts AS alerts,
    MaintenanceHistory AS maintenance_history
FROM {{ source("bronze", "vehicle_health") }}
