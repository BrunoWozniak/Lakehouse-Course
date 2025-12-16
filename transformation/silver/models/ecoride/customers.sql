-- Silver layer: Customers cleaned and standardized
-- Excludes Airbyte metadata columns (_airbyte_*)

{{ config(materialized="table", twin_strategy="allow") }}

SELECT
    id,
    first_name,
    last_name,
    email,
    phone,
    address,
    city,
    state,
    country
FROM {{ source("bronze", "customers") }}