# university-sql-explorer

Normalised academic relational database, credit-weighted aggregation queries, and index plan explorer built with **Python 3.12** and **SQLite**.

## Overview

`university-sql-explorer` models departments, students, modules, and composite-keyed enrolments (`PRIMARY KEY (student_id, module_code, academic_year)`) with SQLite `CHECK` constraints, `FOREIGN KEY` actions, covering indexes, and a small CLI summary runner.

## Features

- **Enforced schema rules**: Restricts credits to `10` / `20` / `40`, marks to `0..100` (or `NULL`), and enrolment years to `2018..2030`, with `PRAGMA foreign_keys = ON` active from connection init.
- **Validated writes**: `add_enrolment()` and `record_mark()` normalise module codes and guard mark bounds in Python before executing SQLite transactions.
- **Weighted academic rollups**: `top_students_by_weighted_average()` weights module marks by credit value and `department_summary()` joins pre-aggregated CTEs so student and module counts do not cross-multiply.
- **Index plan verification**: `explain_module_mark_lookup()` inspects SQLite's `EXPLAIN QUERY PLAN` output to confirm the composite index `idx_enrolments_module_mark` covers threshold lookups.

## Technology Stack

- Python 3.11+ (tested on Python 3.12)
- SQLite3 (`sqlite3` standard library)
- pytest, Ruff

## Installation

```bash
pip install -e ".[dev]"
```

## Usage Examples

Run the built-in CLI against a fresh seeded in-memory database:

```bash
university-sql-explorer
```

Or drive `QueryExplorer` directly in Python:

```python
from sql_explorer.database import QueryExplorer

with QueryExplorer(":memory:") as db:
    db.seed_sample_data()
    print(db.department_summary())
    print(db.top_students_by_weighted_average(min_credits=40))
    print(db.explain_module_mark_lookup("CM2102", 70))
```

## Technical Implementation Details

- `department_summary()` aggregates student counts and module counts in separate CTEs (`student_counts`, `module_counts`) before joining onto `departments` so departments with multiple modules never multiply student headcount.
- Composite index `idx_enrolments_module_mark(module_code, mark)` allows `explain_module_mark_lookup()` to resolve predicates via an index search (`SEARCH` + `COVERING INDEX` where columns match).

## Project Structure

```text
university-sql-explorer/
├── src/sql_explorer/
│   ├── __init__.py
│   └── database.py
├── tests/
│   └── test_database.py
├── pyproject.toml
└── requirements.txt
```

## Testing

```bash
ruff check .
pytest -v
```

## Known Limitations & Future Improvements

- `seed_sample_data()` is idempotent on sample keys via `INSERT OR IGNORE`/`REPLACE`; separating CLI seeding from production usage via an explicit `--seed` flag would keep empty custom DBs untouched.
- Targets SQLite syntax directly; PostgreSQL port would replace `INTEGER PRIMARY KEY` and `PRAGMA` statements with sequences and foreign-key defaults.
