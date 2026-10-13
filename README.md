# ITCS544 Phase 2 — completed implementation and measured evidence

Both datasets are used: 5,511,929 REES46 October events and 284,807 ULB/Worldline credit-card transactions. Read `report/ITCS544_Phase2_Report.pdf` and `docs/DEMO.md` first. The six-task Airflow local test run succeeded in 277.4 seconds. Four contract tests pass. This report is for Phase 2; the in-person demonstration still needs to be delivered by the team.

## What is included

- `data/warehouse.duckdb`: executed warehouse snapshot, constraints, feature mart, and benchmark indexes.
- `data/event_partitions/`: date-partitioned replica used in the measured OLAP comparison.
- `data/session_features.parquet`, `data/session_scores.parquet`: engineered features and scored visits.
- `src/`, `sql/`, `dags/`: complete processing, analysis, and read-only demo code.
- `models/`: fitted transforms/models (load only this trusted project's joblib files).
- `results/`: actual measured results, source hashes, plans, metrics, PR data, review queue, Airflow evidence and test transcript.
- `report/`: final PDF, LaTeX source, IEEE class, and plots; `docs/`: provenance, live-demo guide, requirement map.

The raw archives, temporary staging CSV, Spark intermediates, Python environment and Airflow metadata database are omitted. A full rebuild reacquires them. The database is intentionally DuckDB, replacing the proposed PostgreSQL for this executable environment. No PostgreSQL or production-distributed benchmark is claimed.

## Quick live demo (no downloads required)

Extract both `ITCS544_Phase2_Project.zip` and `ITCS544_Phase2_Database.zip` into the same parent directory so they merge into `ITCS544_Phase2/`. Use Python 3.12, then run from that project directory:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python src/demo.py
.venv/bin/python src/demo.py --query 1
.venv/bin/python src/demo.py --query 4
.venv/bin/python src/demo.py --query 5
.venv/bin/python -m unittest discover -s tests -v
```

The snapshot contains both facts. `src/demo.py` opens it read-only and prints sources, checks, a real SCD history, and model results. All five query numbers are supported. Run scripts from the project root so relative Parquet paths resolve. All code scripts resolve their own project root; direct ad-hoc SQL should use the same working directory.

## Full reproduction

Prerequisites: Python 3.12, Java 17 or compatible Java for PySpark, internet access to the two publisher URLs, approximately 10 GB memory and 15 GB free disk. The run uses two Spark/query/model threads by default. Timings vary by host. Stop all demo/read/write processes before rebuilding the snapshot.

```bash
.venv/bin/python src/run_pipeline.py
.venv/bin/python src/audit_extra.py
.venv/bin/python src/evaluate.py
.venv/bin/python src/figures.py
.venv/bin/python -m unittest discover -s tests -v
```

The sequential runner executes extraction → Spark staging → warehouse/validation → features → five benchmarks → mining. Downloads occur only if the raw files are absent; SHA-256 values identify the assessed sources. Extraction rescans the full original file and deterministically selects complete `(user_id,user_session)` keys within October. The source archive is about 1.74 GB; the card CSV about 151 MB. No Kaggle login is required for the documented direct mirrors.

For the actual Airflow workflow, install and initialize its local metadata DB:

```bash
.venv/bin/python -m pip install 'apache-airflow==2.10.5' 'pydantic==2.10.6' --constraint https://raw.githubusercontent.com/apache/airflow/constraints-2.10.5/constraints-3.12.txt
export AIRFLOW_HOME="$PWD/data/airflow"
export AIRFLOW__CORE__LOAD_EXAMPLES=False
export AIRFLOW__CORE__DAGS_FOLDER="$PWD/dags"
.venv/bin/airflow db migrate
.venv/bin/python dags/phase2_pipeline.py
```

This invokes Airflow `dag.test()` and performs real work, writing task/run metadata locally. It does not require or demonstrate a long-running scheduler. All six tasks are chained with one active run; retries rerun the task. Our successful run's audit is in `results/airflow_status.json` and `results/airflow_run.log`. Airflow's local test recorded null task start/duration fields, so the metadata retains those nulls rather than inventing them; task completion timestamps, script-level measured times, and overall run duration are available.

The Dockerfile provides an optional sequential-run environment (not built/tested here):

```bash
docker build -t itcs544-phase2 .
docker run --rm -v "$PWD/data:/project/data" -v "$PWD/results:/project/results" -v "$PWD/models:/project/models" itcs544-phase2
```

## Rebuild the report

With a LaTeX installation supporting IEEEtran dependencies, after generating the results:

```bash
.venv/bin/python src/figures.py
.venv/bin/python src/build_report.py
cd report
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

`main.template.tex` contains the narrative; `build_report.py` inserts measured tables from JSON/CSV. Some narrative values describe this pinned assessment snapshot and should be reviewed if sources, sampling, splits, or models change. Figures are generated from actual result files. The delivered PDF was visually checked page by page.

## Evaluation semantics

REES46 has no fraud labels. Its Isolation Forest output is a review ranking; the top 100 test visits have blank review labels. MiniBatch K-Means is selected on validation silhouette. Card models use chronological 60/20/20 splits, training-only scaling, and validation-only F1 thresholds. PCA anonymization was performed by the original provider, outside this pipeline; its original fit procedure cannot be audited here. The Random Forest test AP is 0.812, with 57 true positives, 7 false positives, and 18 false negatives. This result applies only to the card benchmark.

Card transaction labels are never joined to clickstream sessions. No shared users, exact card dates, currency equivalence, revenue, or confirmed e-commerce fraud is invented. See report limitations and `docs/SOURCES.md` before interpreting or redistributing source-derived records.
