-- Silver layer: Vehicles catalog cleaned and standardized
-- Excludes Airbyte metadata columns (_airbyte_*)

{{ config(materialized="table", twin_strategy="allow") }}

SELECT
    id,
    model_name,
    model_type,
    color,
    "year",
    "range",
    battery_capacity,
    charging_time
FROM {{ source("bronze", "vehicles") }}