# Phase 2 live demonstration (8–10 minutes)

1. **Purpose and provenance (1 min).** Open report. Explain separate domains: unlabeled e-commerce sessions and labeled credit-card transactions. Both are processed; no customer, currency, or fraud-label join is invented.
2. **Functional warehouse (2 min).** Run `python src/demo.py`. Show counts above 5M, zero integrity failures, and a real SCD2 product history. Open `sql/warehouse.sql` for enforced PK/FK/check constraints and the source-event degenerate key.
3. **ETL execution (1 min).** Open `results/airflow_status.json` and `results/airflow_run.log`. Explain extract → Spark → warehouse validation → feature mart → OLAP → mining. Show quality metrics before/after. A full refresh takes minutes, so launch before the presentation if demonstrating the entire run.
4. **OLAP (2 min).** Run `python src/demo.py --query 1`, then `--query 4` and `--query 5`. Open all five SQL files and `results/benchmarks.json`. Explain warm-cache medians, common result checksums, row pruning, and why scan-friendly native storage often wins.
5. **Mining (2 min).** Open cluster profiles, cluster selection, review queue, and credit-card PR curves. Explain train-only preprocessing, validation-only threshold selection, unseen test periods, and the difference between anomalies and labeled fraud.
6. **Limitations and next steps (1 min).** DuckDB replaces proposed PostgreSQL in this runnable implementation. This is a single-host analytical prototype, not a production deployment. The live presentation and manual anomaly adjudication are human activities still to perform.

Setup and both full rerun methods are in README.md. The delivered snapshot supports the read-only demo without downloading raw data. Do not launch a rebuild while demo readers or another writer are active.
