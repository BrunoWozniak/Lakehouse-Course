-- Silver layer: Product reviews cleaned and standardized
-- Naming: All columns use snake_case convention

{{ config(materialized="table", twin_strategy="allow") }}

WITH formatted_reviews AS (
    SELECT
        CustomerID AS customer_id,
        ReviewID AS review_id,
        CAST("Date" AS DATE) AS review_date,
        Rating AS rating,
        TRIM(ReviewText) AS review_text,
        VehicleModel AS vehicle_model
    FROM {{ source("ecoride_bronze", "ecoride_product_reviews") }}
)

SELECT
    customer_id,
    review_id,
    review_date,
    rating,
    review_text,
    vehicle_model
FROM formatted_reviews