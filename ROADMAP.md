# Lakehouse Course Roadmap

This document outlines planned enhancements for future versions of the Data Lakehouse course.

---

## Version Strategy

### For Students

**Current stable version: v1.0**

```bash
# Option 1: Clone specific version (recommended)
git clone --branch v1.0 https://github.com/BrunoWozniak/Lakehouse.git

# Option 2: Download from GitHub Releases
# Visit: https://github.com/BrunoWozniak/Lakehouse/releases/tag/v1.0
```

### For Maintainers

| Version | Branch | Status |
|---------|--------|--------|
| v1.0 | `main` (tagged) | Stable - for students |
| v2.0 | `v2-dev` | In development |

**Workflow:**
```bash
# Tag stable release
git tag -a v1.0 -m "Course v1.0 - Complete Data Lakehouse"
git push origin v1.0

# Create v2 development branch
git checkout -b v2-dev
git push -u origin v2-dev

# When v2 is ready:
git checkout main
git merge v2-dev
git tag -a v2.0 -m "Course v2.0"
git push origin main --tags
```

---

## Version 2.0 - Planned Features

### Priority 1: High Impact, Moderate Effort

| Feature | Description | Why It Matters |
|---------|-------------|----------------|
| **Real Luxembourg Open Data** | Replace synthetic datasets with authentic open data from data.public.lu | Real data = real learning; local relevance for Luxembourg students |
| **Airbyte-Dagster Integration** | Connect Airbyte to Dagster for orchestrated ingestion | Completes the orchestration story; production-ready pattern |
| **Semantic Layer** | Add dbt Metrics or Cube.dev for business definitions | Industry hot topic; bridges technical and business users |

### Priority 2: Security & Enterprise Readiness

| Feature | Description | Why It Matters |
|---------|-------------|----------------|
| **Keycloak Integration** | Add identity provider for authentication | Enterprise SSO patterns; OAuth2/OIDC fundamentals |
| **RBAC Implementation** | Role-based access control across the stack | Security fundamentals; compliance readiness |
| **Data Contracts** | Define producer/consumer agreements | Trending practice; teaches API thinking for data |

### Priority 3: Advanced Topics

| Feature | Description | Why It Matters |
|---------|-------------|----------------|
| **Streaming Layer** | Kafka → Flink → Iceberg pipeline | Real-time complements batch; complete data picture |
| **CI/CD for Data** | dbt tests + Soda in GitHub Actions | DataOps practices; production readiness |
| **Data Lineage** | OpenLineage integration with Dagster | Governance; impact analysis; debugging |

---

## Parking Lot (Future Consideration)

- **Cost Governance / FinOps** - Cloud cost optimization patterns
- **Data Mesh Architecture** - Domain-oriented decentralization
- **Feature Store** - ML feature management (Feast)
- **Reverse ETL** - Push data back to operational systems
- **Data Catalog** - DataHub or OpenMetadata integration

---

## Design Decisions

### Why Keep Dagster (vs. Airflow)?

| Aspect | Dagster | Airflow |
|--------|---------|---------|
| Developer Experience | Modern, intuitive | Complex, legacy patterns |
| Asset-based Thinking | Native | Bolt-on |
| Testing | Built-in | Manual setup |
| Industry Trajectory | Rising | Mature but stagnant |
| Student Differentiation | Stands out | Everyone knows it |

**Recommendation**: Keep Dagster. Students benefit from learning the modern approach.

---

## Luxembourg Open Data Sources

Potential datasets from [data.public.lu](https://data.public.lu):

| Dataset | Use Case |
|---------|----------|
| Public Transport (Mobiliteit.lu) | Real-time transit analytics |
| Energy Consumption | Sustainability dashboards |
| Air Quality Measurements | Environmental monitoring |
| Business Registry | Company analytics |
| Geographic Boundaries | Spatial analysis |

---

## Contributing

Ideas and contributions welcome! Open an issue to discuss new features.
