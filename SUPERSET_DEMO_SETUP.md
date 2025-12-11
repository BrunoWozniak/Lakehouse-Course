# Superset Quick Setup - Working Configuration! 🎨

## Access Superset
1. Open: http://localhost:8088
2. Login: **admin** / **admin**

## Connect to Dremio (2 minutes)

### Step 1: Add Database Connection
1. Click **Settings** (⚙️ top right) → **Database Connections**
2. Click **+ Database** button
3. Choose **Other** (at the bottom)

### Step 2: Configure Connection
Use this EXACT SQLAlchemy URI:
```
dremio+flight://dremio:dremio123@host.docker.internal:31010/dremio?UseEncryption=false&disableCertificateVerification=true
```

**Important Settings:**:
- Display Name: `Dremio Lakehouse`
- Under "Advanced" → "SQL Lab" tab:
  - ✅ Enable "Allow DML"
  - ✅ Enable "Allow file uploads to database"

### Step 3: Test Connection
1. Click **TEST CONNECTION**
2. Should see "Connection looks good!"
3. Click **CONNECT**

## Create Your First Chart (3 minutes)

### Step 1: Add Dataset
1. Go to **Data** → **Datasets**
2. Click **+ Dataset**
3. Database: `Dremio Lakehouse`
4. Schema: `minio.lakehouse."bronze.ecoride"`
5. Table: `customers_ae0f9e2b-1483-4b02-98c1-bb27e5e135b4.data`
6. Click **CREATE DATASET**

### Step 2: Create Bar Chart - Customer Distribution by City
1. From the dataset, click **Create Chart**
2. Choose **Bar Chart** (first option)
3. Configure:
   - X-Axis: `city`
   - Metric: `COUNT(*)`
   - Sort by: Metric Descending
4. Click **UPDATE CHART**
5. Click **SAVE**
   - Chart name: "Customer Distribution by City"
   - Add to new dashboard: "Lakehouse Demo"

### Step 3: Create Pie Chart - Customer by State
1. Go back to Charts → **+ Chart**
2. Choose your dataset
3. Choose **Pie Chart**
4. Configure:
   - Dimension: `state`
   - Metric: `COUNT(*)`
5. Click **UPDATE CHART**
6. **SAVE** to "Lakehouse Demo" dashboard

### Step 4: Create Big Number - Total Customers
1. Create another chart → **Big Number**
2. Configure:
   - Metric: `COUNT(*)`
   - Subheader: "Total Customers"
3. **UPDATE CHART** → **SAVE**

## View Your Dashboard! 🎉
1. Go to **Dashboards**
2. Click **Lakehouse Demo**
3. You now have 3 visualizations!

## What to Show Students

### During Demo:
1. **Show the connection process** - "Superset connects to any SQL engine"
2. **Create a chart live** - "Business users can self-serve"
3. **Explain the architecture** - "Superset → Dremio → MinIO → Iceberg Tables"
4. **Show filtering** - Click on a bar/pie slice to filter

### Key Messages:
- "No code required for business users"
- "Real-time connection to lakehouse"
- "Any SQL-compatible engine works"
- "Production ready visualization layer"

## Troubleshooting

### If Connection Fails:
1. Try without Flight (Arrow):
```
dremio://dremio:dremio123@host.docker.internal:9047/dremio
```

2. Or use PostgreSQL wire protocol:
```
postgresql+psycopg2://dremio:dremio123@host.docker.internal:31010/dremio
```

### If Charts Don't Load:
- Check Dremio is running: http://localhost:9047
- Verify the table name in Dremio UI
- Use simple COUNT(*) metrics first

## Advanced Features to Mention (Don't Demo):
- Scheduled reports
- Row-level security
- Dashboard filters
- SQL Lab for ad-hoc queries
- Alerts and notifications

## Time Estimate:
- Connection setup: 2 minutes
- First chart: 3 minutes
- Complete dashboard: 10 minutes
- Total demo time: 15 minutes

YOU'RE ALMOST THERE! One more win for the course! 🚀