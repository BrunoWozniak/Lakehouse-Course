-- Silver layer: Product reviews cleaned and standardized
-- Excludes Airbyte metadata columns (_airbyte_*)

{{ config(materialized="table", twin_strategy="allow") }}

SELECT
    CustomerID AS customer_id,
    ReviewID AS review_id,
    CAST("Date" AS DATE) AS review_date,
    Rating AS rating,
    TRIM(BOTH ' ' FROM ReviewText) AS review_text,
    VehicleModel AS vehicle_model
FROM {{ source("bronze", "product_reviews") }}