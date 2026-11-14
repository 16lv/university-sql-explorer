from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Self

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS departments (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    building TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    department_code TEXT NOT NULL,
    enrollment_year INTEGER NOT NULL CHECK(enrollment_year BETWEEN 2018 AND 2030),
    FOREIGN KEY (department_code) REFERENCES departments(code) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS modules (
    module_code TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    department_code TEXT NOT NULL,
    credits INTEGER NOT NULL CHECK(credits IN (10, 20, 40)),
    FOREIGN KEY (department_code) REFERENCES departments(code) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS enrolments (
    student_id INTEGER NOT NULL,
    module_code TEXT NOT NULL,
    academic_year TEXT NOT NULL,
    mark INTEGER CHECK(mark IS NULL OR (mark BETWEEN 0 AND 100)),
    PRIMARY KEY (student_id, module_code, academic_year),
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (module_code) REFERENCES modules(module_code) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_enrolments_module_mark
    ON enrolments(module_code, mark);

CREATE INDEX IF NOT EXISTS idx_students_department
    ON students(department_code);
"""


class QueryExplorer:
    # Small SQLite wrapper for testing university schema constraints, joins, and query plans.

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row
        # SCHEMA_SQL turns on PRAGMA foreign_keys = ON and sets up the 4 tables
        self._conn.executescript(SCHEMA_SQL)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self.close()

    def seed_sample_data(self) -> None:
        self._conn.executemany(
            "INSERT OR IGNORE INTO departments (code, name, building) VALUES (?, ?, ?)",
            [
                ("COMSC", "School of Computer Science and Informatics", "Abacws"),
                ("MATHS", "School of Mathematics", "Abacws"),
            ],
        )
        self._conn.executemany(
            """
            INSERT OR IGNORE INTO students (
                student_id, full_name, email, department_code, enrollment_year
            ) VALUES (?, ?, ?, ?, ?)
            """,
            [
                (240101, "Alex Morgan", "morgana@cardiff.ac.uk", "COMSC", 2024),
                (240102, "Samira Patel", "patels@cardiff.ac.uk", "COMSC", 2024),
                (240103, "Liam Evans", "evansl@cardiff.ac.uk", "COMSC", 2023),
                (240104, "Hannah Rees", "reesh@cardiff.ac.uk", "MATHS", 2024),
            ],
        )
        self._conn.executemany(
            """
            INSERT OR IGNORE INTO modules (
                module_code, title, department_code, credits
            ) VALUES (?, ?, ?, ?)
            """,
            [
                ("CM2102", "Database Systems", "COMSC", 20),
                ("CM2104", "Computational Mathematics", "COMSC", 20),
                ("CM2208", "Scientific Computing", "COMSC", 20),
                ("MA2001", "Linear Algebra", "MATHS", 20),
            ],
        )
        self._conn.executemany(
            """
            INSERT OR REPLACE INTO enrolments (
                student_id, module_code, academic_year, mark
            ) VALUES (?, ?, ?, ?)
            """,
            [
                (240101, "CM2102", "2025/26", 78),
                (240101, "CM2104", "2025/26", 74),
                (240102, "CM2102", "2025/26", 85),
                (240102, "CM2208", "2025/26", 81),
                (240103, "CM2102", "2025/26", 66),
                (240104, "MA2001", "2025/26", 72),
            ],
        )
        self._conn.commit()

    def module_statistics(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT
                m.module_code,
                m.title,
                d.name AS department_name,
                COUNT(e.student_id) AS enrolled_students,
                ROUND(AVG(e.mark), 2) AS average_mark,
                MIN(e.mark) AS min_mark,
                MAX(e.mark) AS max_mark
            FROM modules m
            JOIN departments d ON d.code = m.department_code
            LEFT JOIN enrolments e ON e.module_code = m.module_code
            GROUP BY m.module_code, m.title, d.name
            ORDER BY m.module_code ASC
            """
        ).fetchall()
        return [dict(r) for r in rows]

    def student_transcript(self, student_id: int) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT
                s.student_id,
                s.full_name,
                m.module_code,
                m.title AS module_title,
                m.credits,
                e.academic_year,
                e.mark
            FROM enrolments e
            JOIN students s ON s.student_id = e.student_id
            JOIN modules m ON m.module_code = e.module_code
            WHERE e.student_id = ?
            ORDER BY e.academic_year DESC, m.module_code ASC
            """,
            (student_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def top_students_by_weighted_average(self, min_credits: int = 20) -> list[dict[str, Any]]:
        if min_credits < 0:
            raise ValueError("min_credits must be non-negative.")
        rows = self._conn.execute(
            """
            SELECT
                s.student_id,
                s.full_name,
                s.department_code,
                SUM(m.credits) AS completed_credits,
                ROUND(SUM(e.mark * m.credits) * 1.0 / SUM(m.credits), 2) AS weighted_average
            FROM students s
            JOIN enrolments e ON e.student_id = s.student_id
            JOIN modules m ON m.module_code = e.module_code
            WHERE e.mark IS NOT NULL
            GROUP BY s.student_id, s.full_name, s.department_code
            HAVING SUM(m.credits) >= ?
            ORDER BY weighted_average DESC, s.student_id ASC
            """,
            (min_credits,),
        ).fetchall()
        return [dict(r) for r in rows]

    def explain_module_mark_lookup(self, module_code: str, min_mark: int) -> list[str]:
        clean_code = module_code.strip().upper()
        if not clean_code:
            raise ValueError("module_code must not be blank.")
        if not (0 <= min_mark <= 100):
            raise ValueError("min_mark must be between 0 and 100.")
        rows = self._conn.execute(
            """
            EXPLAIN QUERY PLAN
            SELECT student_id, mark
            FROM enrolments
            WHERE module_code = ? AND mark >= ?
            """,
            (clean_code, min_mark),
        ).fetchall()
        return [str(r["detail"]) for r in rows]
