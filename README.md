# university-sql-explorer

Relational SQLite explorer for university student records, module enrolments, credit-weighted averages, and query-plan inspection using **Python 3.12**.

## Design Notes

- **3NF schema with constraints**: Models `departments`, `students`, `modules`, and `enrolments` with foreign keys (`PRAGMA foreign_keys = ON`) and `CHECK` constraints enforcing valid credit counts and marks (`0..100`).
- **Pre-grouped aggregations**: `module_statistics()` and `top_students_by_weighted_average()` compute credit-weighted marks with explicit float arithmetic (`* 1.0`) and `HAVING` credit thresholds.
- **Query-plan verification**: `explain_module_mark_lookup()` inspects SQLite's `EXPLAIN QUERY PLAN` output to confirm use of the composite `(module_code, mark)` index `idx_enrolments_module_mark`.

## Structure

```text
university-sql-explorer/
├── src/sql_explorer/
│   └── database.py     # Schema DDL, seed fixtures, analytical queries, EXPLAIN helper
├── tests/
│   └── test_database.py
├── pyproject.toml
└── requirements.txt
```

## Development

```bash
pip install -e ".[dev]"
ruff check .
pytest -v
```
