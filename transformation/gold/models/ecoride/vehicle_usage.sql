-- Gold layer: Vehicle usage analytics
-- Aggregates sales and reviews per vehicle model

{% set nessie_branch = var('nessie_branch', 'main') %}

SELECT
    v.id AS vehicle_id,
    v.model_name,
    v.model_type,
    v."year",
    COUNT(s.id) AS total_sales,
    AVG(pr.rating) AS average_rating
FROM {{ source('silver', 'vehicles') }} AT BRANCH {{ nessie_branch }} v
LEFT JOIN {{ source('silver', 'sales') }} AT BRANCH {{ nessie_branch }} s
    ON v.id = s.vehicle_id
LEFT JOIN {{ source('silver', 'product_reviews') }} AT BRANCH {{ nessie_branch }} pr
    ON v.model_name = pr.vehicle_model
GROUP BY v.id, v.model_name, v.model_type, v."year"
