{{ config(
    materialized="view",
    schema="silver"
) }}

-- Simple cleaning model for customers
-- This will create a view in Dremio's lakehouse space
SELECT
    id as customer_id,
    first_name,
    last_name,
    email,
    city,
    "state",
    country,
    -- Add some derived fields
    UPPER(SUBSTRING(first_name, 1, 1)) || UPPER(SUBSTRING(last_name, 1, 1)) as customer_initials,
    CASE
        WHEN country = 'USA' THEN 'Domestic'
        ELSE 'International'
    END as customer_type
FROM minio.lakehouse."bronze.ecoride".customers_ae0f9e2b-1483-4b02-98c1-bb27e5e135b4.data
WHERE email IS NOT NULL  -- Basic data quality filter