-- Silver layer: Charging stations cleaned and standardized
-- Excludes Airbyte metadata columns (_airbyte_*)

{{ config(materialized="table", twin_strategy="allow") }}

SELECT
    id,
    address,
    city,
    state,
    country,
    station_type,
    number_of_chargers,
    operational_status
FROM {{ source("bronze", "stations") }}
