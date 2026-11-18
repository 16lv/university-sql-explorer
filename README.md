# university-sql-explorer

Relational SQLite explorer for student records, module enrolments, credit-weighted averages, and index query-plan verification using **Python 3.12**.

## Design Notes

- **3NF schema with constraints**: Models `departments`, `students`, `modules`, and `enrolments` with composite primary keys (`student_id, module_code, academic_year`), foreign keys (`PRAGMA foreign_keys = ON`), and `CHECK` bounds on credits, enrolment year, and marks (`0..100`).
- **Write & aggregate helpers**: Provides validated `add_enrolment()` and `record_mark()` operations alongside `module_statistics()`, `department_summary()`, and `top_students_by_weighted_average()` (with float credit-weighted math and `HAVING` credit thresholds).
- **Index verification**: `explain_module_mark_lookup()` checks `EXPLAIN QUERY PLAN` to verify lookup coverage via `idx_enrolments_module_mark`.

## Structure

```text
university-sql-explorer/
├── src/sql_explorer/
│   └── database.py     # Schema DDL, seed fixtures, writes, analytical queries, EXPLAIN helper
├── tests/
│   └── test_database.py
├── pyproject.toml
└── requirements.txt
```

## Quick Start

```bash
pip install -e ".[dev]"
ruff check .
pytest -v
```
