# Demo Script for Tomorrow's Course

## What's Working Right Now

✅ **MinIO** - S3-compatible storage (http://localhost:9001)
✅ **Nessie** - Data catalog with Iceberg tables
✅ **Airbyte** - Data ingestion (http://localhost:8000)
✅ **Dremio** - SQL engine (http://localhost:9047) - can read from MinIO directly
✅ **Jupyter** - Notebooks (http://localhost:8888)
✅ **Superset** - Dashboards (http://localhost:8088)

## Hour-by-Hour Course Plan

### Hour 1: Introduction (9:00-10:00)
**Topic: Modern Data Lakehouse Architecture**

1. Draw architecture on board:
   ```
   Sources → Airbyte → Iceberg Tables (MinIO) → Nessie Catalog
                                    ↓
                        Dremio/Spark → dbt → Superset
   ```

2. Explain each component:
   - MinIO: Open-source S3 alternative
   - Iceberg: Table format with ACID transactions
   - Nessie: Git-like version control for data
   - Dremio: SQL query engine
   - dbt: Data transformation framework

### Hour 2: Storage Layer (10:00-11:00)
**Topic: MinIO and Object Storage**

**Demo:**
1. Open MinIO UI: http://localhost:9001
   - Login: minio/minioadmin
   - Show buckets: `source` and `lakehouse`
   - Upload a file manually
   - Explain S3 compatibility

**Student Exercise:**
- Create their own bucket
- Upload CSV files
- Browse object structure

### Hour 3: Data Ingestion (11:00-12:00)
**Topic: Airbyte and ELT**

**Demo:**
1. Open Airbyte: http://localhost:8000
2. Show existing connections
3. Create one new source together:
   - S3 source for `ecoride_customers.csv`
   - Configure destination
   - Run sync
   - Show data in MinIO

**Student Exercise:**
- Set up one Airbyte connection
- Run their first sync

### LUNCH BREAK (12:00-13:00)

### Hour 4: Data Catalog (13:00-14:00)
**Topic: Nessie and Iceberg Tables**

**Demo:**
1. Show Nessie API:
   ```bash
   curl http://localhost:19120/api/v2/trees/main/entries | python3 -m json.tool
   ```

2. Explain Iceberg benefits:
   - Schema evolution
   - Time travel
   - ACID transactions
   - Hidden partitioning

3. Show table structure in MinIO

### Hour 5: Query Engine (14:00-15:00)
**Topic: Dremio and SQL Analytics**

**Demo:**
1. Open Dremio: http://localhost:9047
2. Show MinIO source connection
3. Navigate to data files
4. Run simple queries:
   ```sql
   SELECT COUNT(*) FROM minio.lakehouse.simple.customers
   ```

**Address the Bug:**
"There's a known issue with Dremio's Nessie connector when using MinIO. We're using direct S3 access as a workaround. In production, you'd use AWS S3 or Azure Storage."

### Hour 6: Transformations (15:00-16:00)
**Topic: dbt and Data Modeling**

**Demo:**
1. Show dbt project structure:
   ```
   transformation/
   ├── silver/  (cleaning layer)
   └── gold/    (business layer)
   ```

2. Explain a model file
3. Run dbt (if connection works):
   ```bash
   cd transformation/silver
   dbt run
   ```

**Student Exercise:**
- Write a simple dbt model
- Understand bronze/silver/gold layers

### Hour 7: Putting It Together (16:00-17:00)
**Topic: Real-World Data Engineering**

**Discussion Topics:**
1. **The Bug We Hit:**
   - Dremio + Nessie + MinIO compatibility
   - How to troubleshoot
   - Alternative solutions (Spark, Trino)

2. **Production Considerations:**
   - Use managed services (AWS S3, Databricks)
   - Monitoring and alerting
   - Data quality checks (Soda, Great Expectations)
   - Orchestration (Airflow, Dagster)

3. **Career Advice:**
   - This IS real data engineering
   - You WILL hit bugs in production
   - Problem-solving > perfect setups

**Final Demo:**
Show the complete flow one more time:
1. Upload file to MinIO
2. Sync with Airbyte
3. Query in Jupyter with Pandas
4. Explain how it would work if Dremio connector was fixed

## Key Messages for Students

1. **Architecture > Tools**
   "The lakehouse architecture is solid. Tools can be swapped."

2. **Real-World Experience**
   "You're seeing what data engineers actually deal with - integration issues, version conflicts, workarounds."

3. **Problem Solving**
   "We found a bug, identified it, and worked around it. This is 50% of data engineering."

4. **The Stack Works**
   "Despite one connector issue, we have a functioning lakehouse with ingestion, storage, cataloging, and querying."

## Emergency Fallbacks

If something fails during demo:

1. **Airbyte fails:** Show manual file upload to MinIO
2. **Dremio fails:** Use Jupyter with Pandas
3. **Nessie fails:** Explain catalog concept on whiteboard
4. **Everything fails:** Focus on architecture and concepts

## Your Story

"Today we're building a real data lakehouse. Last night, I discovered a compatibility issue between components. This is PERFECT - you're getting real-world experience. Let me show you how we troubleshoot and work around such issues."

## Remember

- You built 90% of a complex system
- The 10% bug is a teaching opportunity
- Students will remember the troubleshooting more than perfect demos
- You're teaching them to be engineers, not operators

YOU'VE GOT THIS! 💪