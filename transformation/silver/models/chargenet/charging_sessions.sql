{{ config( twin_strategy="allow", materialized="table" ) }}

SELECT
    id,
    station_id,
    session_duration,
    energy_consumed_kWh,
    charging_rate,
    cost,
    start_time,
    end_time
FROM {{ source("chargenet_bronze", "chargenet_charging_sessions") }}
