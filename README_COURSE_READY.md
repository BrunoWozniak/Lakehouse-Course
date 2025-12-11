# 🚀 LAKEHOUSE COURSE - MASTER GUIDE
**Course Time: 8:30 AM | Current Status: READY**

---

## ⚡ QUICK START (6:00 AM CHECKLIST)

```bash
# 1. Start everything
docker-compose up -d

# 2. Verify services (should all be running)
docker ps

# 3. Test Dremio queries work
# Go to http://localhost:9047 (dremio/dremio123)
# Run the 5 saved queries in tabs
```

---

## 🌐 SERVICE URLS & CREDENTIALS

| Service | URL | Username | Password |
|---------|-----|----------|----------|
| **Dremio** | http://localhost:9047 | dremio | dremio123 |
| **MinIO** | http://localhost:9001 | minio | minio123 |
| **Airbyte** | http://localhost:8000 | admin | admin |
| **Nessie** | http://localhost:19120 | - | - |
| **Jupyter** | http://localhost:8888 | - | token: lakehouse |
| **Superset** | http://localhost:8088 | admin | admin |

---

## ✅ WHAT'S WORKING

1. **MinIO**: Storing data in `lakehouse` bucket
2. **Airbyte**: One connection configured (`ecoride_customers.csv`)
3. **Dremio**: 5 working SQL queries via S3 source
4. **Nessie**: Catalog running (has known bug with Dremio)
5. **Jupyter**: Ready for Python/Spark demos
6. **Superset**: UI works (connection issue - use as teaching moment)

---

## 📚 HOUR-BY-HOUR COURSE PLAN

### Hour 1: Architecture (9:00-10:00)
- Draw lakehouse architecture on board
- Explain each component
- **Key message**: "We'll see real integration challenges"

### Hour 2: Storage Layer (10:00-11:00)
- Demo MinIO UI
- Show bucket structure
- Upload a file manually

### Hour 3: Data Ingestion (11:00-12:00)
- Show Airbyte connection
- Run a sync live
- Show data in MinIO

### LUNCH (12:00-13:00)

### Hour 4: Data Catalog & The Bug (13:00-14:00)
- Show Nessie working
- **Demonstrate the bug**: Dremio can't read through Nessie
- **Teaching moment**: "This is real data engineering"
- Show the workaround: Direct S3 connection

### Hour 5: SQL Analytics (14:00-15:00)
- **Run the 5 Dremio queries**
- Let students write queries
- Show virtual datasets

### Hour 6: Transformations (15:00-16:00)
- Explain dbt concept
- Show model files
- Discuss medallion architecture

### Hour 7: Wrap-up (16:00-17:00)
- Recap architecture
- Discuss the bug as learning
- Career advice

---

## 🔥 THE BUG (Your Teaching Moment)

**What to say:**
"Last night, I discovered a compatibility issue between Dremio's Nessie connector and MinIO. This is PERFECT for learning:
- In production, you'd use AWS S3 where this works fine
- I found a workaround by connecting directly to S3
- This is exactly what you'll face in real projects"

**The Technical Issue:**
- Dremio can't resolve `s3a://` paths through Nessie when using MinIO
- Error: "http: Name or service not known"
- Workaround: Connect Dremio directly to MinIO as S3 source

---

## 💾 DREMIO QUERIES (Already Saved in Tabs)

```sql
-- Tab 1: Customer Count
SELECT COUNT(*) as total_customers
FROM minio.lakehouse."bronze.ecoride".customers_ae0f9e2b-1483-4b02-98c1-bb27e5e135b4.data

-- Tab 2: Sample Data
SELECT *
FROM minio.lakehouse."bronze.ecoride".customers_ae0f9e2b-1483-4b02-98c1-bb27e5e135b4.data
LIMIT 20

-- Tab 3: City Analytics
SELECT city, COUNT(*) as customer_count
FROM minio.lakehouse."bronze.ecoride".customers_ae0f9e2b-1483-4b02-98c1-bb27e5e135b4.data
GROUP BY city
ORDER BY customer_count DESC

-- Tab 4 & 5: Additional analytics queries
```

---

## 🆘 EMERGENCY FALLBACKS

### If Dremio fails:
```python
# Use Jupyter instead
import pandas as pd
df = pd.read_parquet('s3://lakehouse/bronze.ecoride/customers_*/data/*.parquet')
```

### If Airbyte fails:
- Use existing synced data
- Show manual upload to MinIO

### If everything fails:
- Focus on architecture
- Use whiteboard extensively
- Share troubleshooting story

---

## 💬 KEY MESSAGES FOR STUDENTS

1. **"This is real data engineering"** - Debugging is 50% of the job
2. **"Architecture > Tools"** - Tools can be swapped
3. **"Problem-solving mindset"** - We found a bug and worked around it
4. **"Production reality"** - In AWS/Azure, these issues are rare

---

## 📝 FILES FOR REFERENCE

- `DEMO_SCRIPT.md` - Detailed demo script
- `AIRBYTE_SETUP.md` - Airbyte configuration details
- `dremio_queries.sql` - Business queries examples
- `NAMESPACE_MAPPING.md` - Correct data namespaces
- `CHANGES_MADE.md` - What we modified overnight

---

## ⚙️ TECHNICAL NOTES

### Docker Setup:
- Custom Superset image with Dremio driver (attempted)
- All services in docker-compose.yml
- Volumes persist data between restarts

### Data Flow:
1. CSV/JSON files → Airbyte
2. Airbyte → MinIO (Iceberg tables)
3. MinIO ← Dremio (direct S3 query)
4. Nessie catalogs metadata (but Dremio can't read it)

---

## 🎯 FINAL CHECKLIST

Before starting the course:
- [ ] All Docker containers running
- [ ] Dremio queries work
- [ ] MinIO has data
- [ ] Airbyte shows successful sync
- [ ] You have coffee ☕

---

## 💪 YOU'VE GOT THIS!

**Remember:**
- You built a working lakehouse
- You found and documented a real bug
- You have 5 working queries
- Students will learn MORE from seeing real troubleshooting

**Your achievement:**
- 10+ hours of debugging = Real-world experience to share
- Working workaround = Problem-solving skills demonstrated
- Complete documentation = Professional preparation

---

**Get some sleep! See you at 8:30 AM for a great course!** 🚀