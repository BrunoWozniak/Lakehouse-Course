-- Silver layer: Sales transactions cleaned and standardized
-- Excludes Airbyte metadata columns (_airbyte_*)

{{ config(materialized="table", twin_strategy="allow") }}

SELECT
    id,
    customer_id,
    vehicle_id,
    TO_DATE(sale_date, 'MM/DD/YYYY', 1) AS sale_date,
    CAST(sale_price AS DOUBLE) AS sale_price,
    payment_method
FROM {{ source("bronze", "sales") }}
