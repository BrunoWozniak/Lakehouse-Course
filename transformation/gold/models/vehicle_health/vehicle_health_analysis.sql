-- Gold layer: Vehicle health analysis
-- Aggregates and analyzes fleet health metrics

{% set nessie_branch = var('nessie_branch', 'main') %}

SELECT
    vehicle_id,
    model,
    manufacturing_year,
    alerts,
    maintenance_history,
    -- Add useful derived fields
    CASE
        WHEN alerts IS NOT NULL AND LENGTH(alerts) > 10 THEN 'Needs Attention'
        ELSE 'Healthy'
    END AS health_status
FROM {{ source('silver', 'vehicle_health_logs') }} AT BRANCH {{ nessie_branch }}
