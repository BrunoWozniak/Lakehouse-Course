-- Silver layer: Charging sessions cleaned and standardized
-- Excludes Airbyte metadata columns (_airbyte_*)
-- NOTE: Column names may need adjustment based on actual Bronze schema

{{ config(materialized="table", twin_strategy="allow") }}

SELECT
    id,
    station_id,
    session_duration,
    energy_consumed_kWh,
    charging_rate,
    cost,
    start_time,
    end_time
FROM {{ source("bronze", "charging_sessions") }}
