-- Silver layer: Vehicle health logs cleaned and standardized
-- Naming: All columns use snake_case convention

{{ config(materialized="table", twin_strategy="allow") }}

SELECT
    VehicleID AS vehicle_id,
    Model AS model,
    ManufacturingYear AS manufacturing_year,
    Alerts AS alerts,
    MaintenanceHistory AS maintenance_history
FROM {{ source("vehicle_health_bronze", "vehicle_health_logs") }}
