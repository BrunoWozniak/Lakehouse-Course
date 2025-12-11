{{ config(materialized="table", twin_strategy="allow") }}

-- Gold layer: Enriched customer data with aggregated metrics
-- Source: Silver layer customers table

SELECT
    c.id as customer_id,
    c.first_name,
    c.email,
    c.city,
    c.state,
    c.country,
    -- Add derived fields for analytics
    UPPER(c.country) as country_code,
    CONCAT(c.city, ', ', c.state) as location
FROM {{ source('silver', 'customers') }} c
