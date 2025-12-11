# Correct Namespace Mappings for All Files

## Files and Their Correct Namespaces

Based on dbt sources.yml, here are the EXACT namespaces to use in Airbyte:

| File Name | Airbyte Namespace | Table Name | Primary Key | Notes |
|-----------|-------------------|------------|-------------|--------|
| `ecoride_customers.csv` | `bronze.ecoride` | `customers` | `id` | ✓ Matches dbt |
| `ecoride_sales.csv` | `bronze.ecoride` | `sales` | `id` or `sale_id` | ✓ Matches dbt |
| `ecoride_vehicles.csv` | `bronze.ecoride` | `vehicles` | `vehicle_id` | ✓ Matches dbt |
| `ecoride_product_reviews.json` | `bronze.ecoride` | `product_reviews` | `review_id` | ✓ Matches dbt |
| `chargenet_stations.json` | `bronze.chargenet` | `stations` | `station_id` | ✓ Matches dbt |
| `chargenet_charging_sessions.json` | `bronze.chargenet` | `charging_sessions` | `session_id` | ✓ Matches dbt |
| `vehicle_health_data.json` | `bronze.vehicle_health` | `logs` | `log_id` | ⚠️ Table name is `logs` not `vehicle_health_data` |

## IMPORTANT NOTES

1. **Vehicle Health**: The file is `vehicle_health_data.json` but the table name should be `logs` to match dbt

2. **Namespace Structure**:
   - `bronze` = Layer (raw data)
   - `ecoride/chargenet/vehicle_health` = Source system
   - Table name = Entity (customers, sales, etc.)

3. **In Nessie/Iceberg**, this creates:
   - `bronze.ecoride.customers`
   - `bronze.ecoride.sales`
   - `bronze.ecoride.vehicles`
   - `bronze.ecoride.product_reviews`
   - `bronze.chargenet.stations`
   - `bronze.chargenet.charging_sessions`
   - `bronze.vehicle_health.logs`

4. **In MinIO**, files will be stored at:
   - `lakehouse/bronze/ecoride/customers_[uuid]/`
   - `lakehouse/bronze/ecoride/sales_[uuid]/`
   - etc.

## For Tomorrow's Demo

Start with just these two:
1. `ecoride_customers.csv` → `bronze.ecoride.customers`
2. `chargenet_stations.json` → `bronze.chargenet.stations`

This gives you one CSV and one JSON to demonstrate both file types.

## dbt Will Look For

The dbt models expect these exact source names:
```yaml
sources:
  - name: ecoride_bronze
    database: catalog
    schema: bronze.ecoride
    tables:
      - name: customers
      - name: sales
      - name: vehicles
      - name: product_reviews

  - name: chargenet_bronze
    database: catalog
    schema: bronze.chargenet
    tables:
      - name: charging_sessions
      - name: stations

  - name: vehicle_health_bronze
    database: catalog
    schema: bronze.vehicle_health
    tables:
      - name: logs
```

So the namespaces MUST match exactly as shown in the table above!