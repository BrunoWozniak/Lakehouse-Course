-- Silver layer: Sales transactions cleaned and standardized

{{ config(materialized="table", twin_strategy="allow") }}

SELECT
    id,
    customer_id,
    vehicle_id,
    TO_DATE(sale_date, 'MM/DD/YYYY') AS sale_date,
    sale_price,
    payment_method
FROM {{ source("ecoride_bronze", "ecoride_sales") }}
