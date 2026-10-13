# Phase 2 assignment coverage

| Required item | Implemented evidence | Status |
|---|---|---|
| ≥5M raw records | 5,511,929 selected clickstream events, plus 284,807 cards; source manifest | Executed |
| Both datasets used | Separate event/card facts, session mining, labeled card experiments | Executed |
| Multi-tier architecture | Raw → Spark staging → DuckDB warehouse → OLAP/features/models | Executed locally |
| Full logical/physical ERD | Report Fig. 2 and complete `sql/warehouse.sql` | Complete |
| Bus matrix / facts / dimensions | Report table and grain definitions | Complete |
| SCD Type 2 | 128,525 observed product versions, temporal-pair interval validation | Executed |
| Degenerate dimensions | Stable source event/transaction row keys tied to pinned source manifests | Implemented |
| Automated ETL | Six real Airflow tasks, successful `dag.test()` execution | Executed |
| Validation/imputation/deduplication | Explicit schema/quality flags; Unknown members; replay-safe row keys; observed repeats retained and audited | Executed |
| Before/after quality | `staging_quality.json`, `extra_quality.json`, `warehouse_checks.json` | Measured |
| Five complex OLAP queries | q1–q5 SQL, three physical strategies, 45 timed SELECTs plus warm-ups, query plans and parity hashes | Measured |
| Mining preparation/features/EDA | Temporal splits, 18 session features, training-only transforms, EDA figures | Executed |
| Preliminary baseline results | Velocity, Isolation Forest, MiniBatch K-Means, amount, logistic regression, Random Forest | Measured |
| IEEE/ACM PDF ≤8 pages | Final IEEE conference PDF | Complete |
| Live code demonstration | Executed read-only demo; `docs/DEMO.md` presentation guide | Prepared; team must present |

Phase 1 deployment change: DuckDB replaces PostgreSQL in the working implementation. PySpark runs locally on two local execution threads rather than a distributed cluster. No claim is made that an instructor has accepted the change, that the work has been submitted, or that the live presentation has happened.

Next-phase work: human anomaly adjudication, duplicate/feature sensitivity checks, group-aware temporal evaluation where metadata permits, cluster-relative anomalies, optional deep/density models, broader workload/load testing and actual container deployment validation.
