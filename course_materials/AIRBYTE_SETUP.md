# Airbyte Configuration for All 7 Files

Open Airbyte at http://localhost:8000

## Destination (Already Set Up)
- Name: `Lakehouse`
- Type: S3 Data Lake
- Format: Apache Iceberg

## Create 7 Sources (One for Each File)

### Source 1: EcoRide Customers
- **Source Type:** S3
- **Name:** `S3 - ecoride_customers`
- **Bucket:** `source`
- **Globs:** `ecoride_customers.csv`
- **Delivery Method:** `Replicate Records`
- **File Format:** `CSV`
- **S3 Endpoint:** `http://host.docker.internal:9000`
- **Access Key:** `minio`
- **Secret Key:** `minioadmin`

**Connection Settings:**
- Namespace: `bronze.ecoride`
- Table Name: `customers`
- Primary Key: `id`

---

### Source 2: EcoRide Sales (or Rides)
- **Source Type:** S3
- **Name:** `S3 - ecoride_sales`
- **Bucket:** `source`
- **Globs:** `ecoride_sales.csv`
- **Delivery Method:** `Replicate Records`
- **File Format:** `CSV`
- **S3 Endpoint:** `http://host.docker.internal:9000`
- **Access Key:** `minio`
- **Secret Key:** `minioadmin`

**Connection Settings:**
- Namespace: `bronze.ecoride`
- Table Name: `sales`
- Primary Key: `id`

---

### Source 3: EcoRide Vehicles
- **Source Type:** S3
- **Name:** `S3 - ecoride_vehicles`
- **Bucket:** `source`
- **Globs:** `ecoride_vehicles.csv`
- **Delivery Method:** `Replicate Records`
- **File Format:** `CSV`
- **S3 Endpoint:** `http://host.docker.internal:9000`
- **Access Key:** `minio`
- **Secret Key:** `minioadmin`

**Connection Settings:**
- Namespace: `bronze.ecoride`
- Table Name: `vehicles`
- Primary Key: `vehicle_id`

---

### Source 4: ChargeNet Stations
- **Source Type:** S3
- **Name:** `S3 - chargenet_stations`
- **Bucket:** `source`
- **Globs:** `chargenet_stations.json`
- **Delivery Method:** `Replicate Records`
- **File Format:** `JSON`
- **Reader Options:** `{"multiLine": true}`
- **S3 Endpoint:** `http://host.docker.internal:9000`
- **Access Key:** `minio`
- **Secret Key:** `minioadmin`

**Connection Settings:**
- Namespace: `bronze.chargenet`
- Table Name: `stations`
- Primary Key: `station_id`

---

### Source 5: ChargeNet Charging Sessions
- **Source Type:** S3
- **Name:** `S3 - chargenet_sessions`
- **Bucket:** `source`
- **Globs:** `chargenet_charging_sessions.json`
- **Delivery Method:** `Replicate Records`
- **File Format:** `JSON`
- **Reader Options:** `{"multiLine": true}`
- **S3 Endpoint:** `http://host.docker.internal:9000`
- **Access Key:** `minio`
- **Secret Key:** `minioadmin`

**Connection Settings:**
- Namespace: `bronze.chargenet`
- Table Name: `charging_sessions`
- Primary Key: `session_id`

---

### Source 6: Vehicle Health Data
- **Source Type:** S3
- **Name:** `S3 - vehicle_health`
- **Bucket:** `source`
- **Globs:** `vehicle_health_data.json`
- **Delivery Method:** `Replicate Records`
- **File Format:** `JSON`
- **Reader Options:** `{"multiLine": true}`
- **S3 Endpoint:** `http://host.docker.internal:9000`
- **Access Key:** `minio`
- **Secret Key:** `minioadmin`

**Connection Settings:**
- Namespace: `bronze.vehicle`
- Table Name: `health_data`
- Primary Key: `log_id`

---

### Source 7: EcoRide Product Reviews
- **Source Type:** S3
- **Name:** `S3 - product_reviews`
- **Bucket:** `source`
- **Globs:** `ecoride_product_reviews.json`
- **Delivery Method:** `Replicate Records`
- **File Format:** `JSON`
- **Reader Options:** `{"multiLine": true}`
- **S3 Endpoint:** `http://host.docker.internal:9000`
- **Access Key:** `minio`
- **Secret Key:** `minioadmin`

**Connection Settings:**
- Namespace: `bronze.ecoride`
- Table Name: `product_reviews`
- Primary Key: `review_id`

---

## Quick Setup Process

For each source:
1. Click "Sources" → "+ New source"
2. Select "S3"
3. Fill in the details above
4. Click "Set up source"
5. Go to "Connections" → "+ New connection"
6. Select the source and "Lakehouse" destination
7. Configure namespace and table name
8. Set primary key
9. Save and sync

## After All 7 Are Set Up

Run all syncs. Each should take 1-2 minutes.

You'll have:
- `bronze.ecoride.customers`
- `bronze.ecoride.sales`
- `bronze.ecoride.vehicles`
- `bronze.ecoride.product_reviews`
- `bronze.chargenet.stations`
- `bronze.chargenet.charging_sessions`
- `bronze.vehicle.health_data`

All as Iceberg tables in MinIO, cataloged in Nessie!