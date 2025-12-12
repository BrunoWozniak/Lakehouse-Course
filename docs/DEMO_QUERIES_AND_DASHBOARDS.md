# Demo Queries and Dashboards

## Dremio Demo Queries (Simple → Advanced)

Use these in Dremio SQL Editor: http://localhost:9047

---

### Level 1: Basic Queries (Warmup)

```sql
-- Q1: Count customers
SELECT COUNT(*) AS total_customers
FROM catalog.silver.customers;

-- Q2: View first 10 customers
SELECT * FROM catalog.silver.customers LIMIT 10;

-- Q3: Customers by state
SELECT state, COUNT(*) AS customer_count
FROM catalog.silver.customers
GROUP BY state
ORDER BY customer_count DESC;
```

---

### Level 2: Aggregations (Intermediate)

```sql
-- Q4: Total sales by payment method
SELECT
    payment_method,
    COUNT(*) AS num_sales,
    SUM(sale_price) AS total_revenue,
    AVG(sale_price) AS avg_sale
FROM catalog.silver.sales
GROUP BY payment_method
ORDER BY total_revenue DESC;

-- Q5: Monthly sales trend
SELECT
    DATE_TRUNC('month', sale_date) AS month,
    COUNT(*) AS num_sales,
    SUM(sale_price) AS revenue
FROM catalog.silver.sales
GROUP BY DATE_TRUNC('month', sale_date)
ORDER BY month;

-- Q6: Average rating by vehicle model
SELECT
    vehicle_model,
    COUNT(*) AS num_reviews,
    AVG(rating) AS avg_rating,
    MIN(rating) AS min_rating,
    MAX(rating) AS max_rating
FROM catalog.silver.product_reviews
GROUP BY vehicle_model
ORDER BY avg_rating DESC;
```

---

### Level 3: JOINs (Advanced)

```sql
-- Q7: Sales with customer info
SELECT
    s.id AS sale_id,
    c.first_name,
    c.email,
    c.city,
    s.sale_price,
    s.sale_date
FROM catalog.silver.sales s
JOIN catalog.silver.customers c ON s.customer_id = c.id
ORDER BY s.sale_date DESC
LIMIT 20;

-- Q8: Top 10 customers by total spend
SELECT
    c.id,
    c.first_name,
    c.email,
    COUNT(s.id) AS num_purchases,
    SUM(s.sale_price) AS total_spent
FROM catalog.silver.customers c
JOIN catalog.silver.sales s ON c.id = s.customer_id
GROUP BY c.id, c.first_name, c.email
ORDER BY total_spent DESC
LIMIT 10;

-- Q9: Charging station utilization
SELECT
    st.id AS station_id,
    st.city,
    st.station_type,
    COUNT(cs.id) AS total_sessions,
    SUM(cs.energy_consumed_kWh) AS total_energy_kwh,
    AVG(cs.session_duration) AS avg_duration_mins
FROM catalog.silver.stations st
LEFT JOIN catalog.silver.charging_sessions cs ON st.id = cs.station_id
GROUP BY st.id, st.city, st.station_type
ORDER BY total_sessions DESC;
```

---

### Level 4: Window Functions & CTEs (Expert)

```sql
-- Q10: Customer purchase rank
WITH customer_totals AS (
    SELECT
        c.id,
        c.first_name,
        c.city,
        SUM(s.sale_price) AS total_spent
    FROM catalog.silver.customers c
    JOIN catalog.silver.sales s ON c.id = s.customer_id
    GROUP BY c.id, c.first_name, c.city
)
SELECT
    *,
    RANK() OVER (ORDER BY total_spent DESC) AS spending_rank,
    PERCENT_RANK() OVER (ORDER BY total_spent DESC) AS spending_percentile
FROM customer_totals
ORDER BY spending_rank
LIMIT 20;

-- Q11: Running total of sales over time
SELECT
    sale_date,
    sale_price,
    SUM(sale_price) OVER (ORDER BY sale_date) AS running_total,
    AVG(sale_price) OVER (
        ORDER BY sale_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS moving_avg_7
FROM catalog.silver.sales
ORDER BY sale_date;

-- Q12: Charging session anomaly detection
WITH session_stats AS (
    SELECT
        station_id,
        energy_consumed_kWh,
        AVG(energy_consumed_kWh) OVER (PARTITION BY station_id) AS station_avg,
        STDDEV(energy_consumed_kWh) OVER (PARTITION BY station_id) AS station_stddev
    FROM catalog.silver.charging_sessions
)
SELECT *,
    CASE
        WHEN ABS(energy_consumed_kWh - station_avg) > 2 * station_stddev THEN 'ANOMALY'
        ELSE 'NORMAL'
    END AS status
FROM session_stats
WHERE ABS(energy_consumed_kWh - station_avg) > 2 * station_stddev;
```

---

### Level 5: Iceberg Time Travel (Lakehouse Feature!)

```sql
-- Q13: Query historical data (time travel)
-- See data as it was 1 hour ago
SELECT * FROM catalog.bronze.ecoride_customers
AT TIMESTAMP AS OF TIMESTAMPADD(HOUR, -1, CURRENT_TIMESTAMP)
LIMIT 10;

-- Q14: View table history
SELECT * FROM TABLE(table_history('catalog.bronze.ecoride_customers'));

-- Q15: View snapshots
SELECT * FROM TABLE(table_snapshot('catalog.bronze.ecoride_customers'));
```

---

## Superset Dashboard Design

### Dashboard: "EV Lakehouse Analytics"

Create these 5 charts for a comprehensive dashboard:

---

### Chart 1: Big Number - Key Metrics (Row of 4)

**Type**: Big Number with Trendline

| Metric | SQL | Description |
|--------|-----|-------------|
| Total Customers | `SELECT COUNT(*) FROM catalog.silver.customers` | Customer count |
| Total Revenue | `SELECT SUM(sale_price) FROM catalog.silver.sales` | Revenue |
| Avg Rating | `SELECT AVG(rating) FROM catalog.silver.product_reviews` | Product rating |
| Active Stations | `SELECT COUNT(*) FROM catalog.silver.stations WHERE operational_status='Active'` | Stations |

**Layout**: 4 big numbers across the top row

---

### Chart 2: Sales by State (Map or Bar Chart)

**Type**: Bar Chart (horizontal)

```sql
SELECT
    c.state,
    SUM(s.sale_price) AS total_sales,
    COUNT(*) AS num_transactions
FROM catalog.silver.sales s
JOIN catalog.silver.customers c ON s.customer_id = c.id
GROUP BY c.state
ORDER BY total_sales DESC
```

**Configuration**:
- X-axis: `total_sales`
- Y-axis: `state`
- Sort: By value descending

---

### Chart 3: Monthly Revenue Trend (Line Chart)

**Type**: Time-series Line Chart

```sql
SELECT
    DATE_TRUNC('month', sale_date) AS month,
    SUM(sale_price) AS revenue,
    COUNT(*) AS transactions
FROM catalog.silver.sales
GROUP BY DATE_TRUNC('month', sale_date)
ORDER BY month
```

**Configuration**:
- X-axis: `month` (time)
- Y-axis: `revenue`
- Add `transactions` as secondary metric

---

### Chart 4: Product Reviews by Vehicle Model (Radar/Bar)

**Type**: Bar Chart with Colors

```sql
SELECT
    vehicle_model,
    rating,
    COUNT(*) AS count
FROM catalog.silver.product_reviews
GROUP BY vehicle_model, rating
ORDER BY vehicle_model, rating
```

**Configuration**:
- X-axis: `vehicle_model`
- Y-axis: `count`
- Color: `rating` (1-5 color scale)

---

### Chart 5: Charging Station Heatmap (Pivot Table)

**Type**: Pivot Table or Heatmap

```sql
SELECT
    city,
    station_type,
    SUM(total_sessions) AS sessions,
    SUM(total_energy) AS energy_kwh
FROM (
    SELECT
        st.city,
        st.station_type,
        COUNT(cs.id) AS total_sessions,
        SUM(cs.energy_consumed_kWh) AS total_energy
    FROM catalog.silver.stations st
    LEFT JOIN catalog.silver.charging_sessions cs ON st.id = cs.station_id
    GROUP BY st.city, st.station_type
) sub
GROUP BY city, station_type
```

**Configuration**:
- Rows: `city`
- Columns: `station_type`
- Values: `sessions` (color by intensity)

---

### Dashboard Layout

```
┌────────────────────────────────────────────────────────────────────┐
│  [Total Customers]  [Total Revenue]  [Avg Rating]  [Active Stations]│
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────────────────┐  ┌────────────────────────────────┐  │
│  │   Sales by State        │  │   Monthly Revenue Trend        │  │
│  │   (Bar Chart)           │  │   (Line Chart)                 │  │
│  │                         │  │                                │  │
│  └─────────────────────────┘  └────────────────────────────────┘  │
│                                                                    │
│  ┌─────────────────────────┐  ┌────────────────────────────────┐  │
│  │   Reviews by Model      │  │   Charging Station Heatmap     │  │
│  │   (Bar Chart)           │  │   (Pivot Table)                │  │
│  │                         │  │                                │  │
│  └─────────────────────────┘  └────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

---

## Soda Bad Data Demo

### Test Scenario: Introduce Bad Data

1. **Run initial Soda scan** (all should pass):
```bash
docker exec dagster soda scan -d lakehouse -c /app/soda/configuration.yml /app/soda/checks/silver_checks.yml
```

2. **Inject bad data** (duplicate ID, missing email):
```sql
-- In Dremio, insert bad record
INSERT INTO catalog.bronze.ecoride_customers
VALUES (1, 'Duplicate User', 'bad@email', 'Test City', 'XX', 'Test');
```

3. **Run Soda scan again** - watch failures:
```bash
docker exec dagster soda scan -d lakehouse -c /app/soda/configuration.yml /app/soda/checks/silver_checks.yml
```

Expected failures:
- ❌ `duplicate_count(id) = 0` → FAILED (found 1 duplicate)
- ⚠️ `invalid_count(email) = 0` → WARNING (invalid format)

4. **Fix the data and re-run**:
```sql
DELETE FROM catalog.bronze.ecoride_customers WHERE id = 1 AND first_name = 'Duplicate User';
```

This demonstrates the data quality feedback loop!
