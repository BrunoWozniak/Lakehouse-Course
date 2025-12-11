-- Dremio Queries to Promote and Query Data
-- After Airbyte syncs complete, use these in Dremio

-- Step 1: Create a Space for organized access
CREATE SPACE lakehouse;

-- Step 2: After promoting Parquet folders as datasets in UI,
-- create Virtual Datasets for easy access

-- EcoRide Tables
CREATE VDS lakehouse.customers AS
SELECT * FROM minio.lakehouse.bronze."bronze.ecoride".[customers_folder].data
LIMIT 10000;

CREATE VDS lakehouse.sales AS
SELECT * FROM minio.lakehouse.bronze."bronze.ecoride".[sales_folder].data
LIMIT 10000;

CREATE VDS lakehouse.vehicles AS
SELECT * FROM minio.lakehouse.bronze."bronze.ecoride".[vehicles_folder].data
LIMIT 10000;

CREATE VDS lakehouse.product_reviews AS
SELECT * FROM minio.lakehouse.bronze."bronze.ecoride".[product_reviews_folder].data
LIMIT 10000;

-- ChargeNet Tables
CREATE VDS lakehouse.stations AS
SELECT * FROM minio.lakehouse.bronze."bronze.chargenet".[stations_folder].data
LIMIT 10000;

CREATE VDS lakehouse.charging_sessions AS
SELECT * FROM minio.lakehouse.bronze."bronze.chargenet".[charging_sessions_folder].data
LIMIT 10000;

-- Vehicle Health
CREATE VDS lakehouse.vehicle_health AS
SELECT * FROM minio.lakehouse.bronze."bronze.vehicle".[health_data_folder].data
LIMIT 10000;

-- Step 3: Business Queries for Demo

-- Customer Analysis
SELECT
    COUNT(*) as total_customers,
    COUNT(DISTINCT city) as cities_served
FROM lakehouse.customers;

-- Sales Performance
SELECT
    DATE_TRUNC('month', sale_date) as month,
    COUNT(*) as total_sales,
    SUM(amount) as revenue
FROM lakehouse.sales
GROUP BY 1
ORDER BY 1;

-- Charging Station Utilization
SELECT
    s.station_name,
    COUNT(cs.session_id) as total_sessions,
    AVG(cs.duration_minutes) as avg_duration
FROM lakehouse.stations s
LEFT JOIN lakehouse.charging_sessions cs ON s.station_id = cs.station_id
GROUP BY s.station_name
ORDER BY total_sessions DESC
LIMIT 10;

-- Vehicle Health Analysis
SELECT
    vehicle_id,
    COUNT(*) as alert_count,
    COUNT(DISTINCT DATE(timestamp)) as days_with_alerts
FROM lakehouse.vehicle_health
WHERE alert_level = 'HIGH'
GROUP BY vehicle_id
ORDER BY alert_count DESC
LIMIT 10;

-- Customer Lifetime Value (Simple)
SELECT
    c.customer_id,
    c.first_name,
    c.last_name,
    COUNT(s.sale_id) as purchase_count,
    SUM(s.amount) as total_spent,
    AVG(s.amount) as avg_purchase
FROM lakehouse.customers c
LEFT JOIN lakehouse.sales s ON c.customer_id = s.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name
ORDER BY total_spent DESC
LIMIT 100;