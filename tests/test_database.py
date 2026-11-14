from __future__ import annotations

import sqlite3

import pytest

from src.sql_explorer.database import QueryExplorer


def test_relational_joins_aggregations_and_constraints() -> None:
    explorer = QueryExplorer(":memory:")
    explorer.seed_sample_data()

    stats = explorer.module_statistics()
    cm2102 = next(m for m in stats if m["module_code"] == "CM2102")
    assert cm2102["enrolled_students"] == 3
    assert cm2102["average_mark"] == 76.33
    assert cm2102["min_mark"] == 66
    assert cm2102["max_mark"] == 85

    transcript = explorer.student_transcript(240101)
    assert len(transcript) == 2
    assert transcript[0]["module_code"] == "CM2102"

    ranking = explorer.top_students_by_weighted_average(min_credits=40)
    assert len(ranking) == 2
    assert ranking[0]["full_name"] == "Samira Patel"
    assert ranking[0]["weighted_average"] == 83.0


def test_foreign_key_and_check_constraints_reject_invalid_rows() -> None:
    explorer = QueryExplorer(":memory:")
    explorer.seed_sample_data()

    # Mark above 100 violates CHECK(mark BETWEEN 0 AND 100)
    with pytest.raises(sqlite3.IntegrityError):
        explorer._conn.execute(
            "INSERT INTO enrolments (student_id, module_code, academic_year, mark) VALUES (?, ?, ?, ?)",
            (240101, "CM2102", "2026/27", 145),
        )


def test_composite_index_is_used_by_query_planner() -> None:
    explorer = QueryExplorer(":memory:")
    explorer.seed_sample_data()

    plan = explorer.explain_module_mark_lookup("CM2102", 70)
    assert any("idx_enrolments_module_mark" in detail for detail in plan)


def test_query_explorer_validates_arguments_and_context_manager() -> None:
    with QueryExplorer(":memory:") as explorer:
        explorer.seed_sample_data()
        with pytest.raises(ValueError, match="non-negative"):
            explorer.top_students_by_weighted_average(min_credits=-5)
        with pytest.raises(ValueError, match="between 0 and 100"):
            explorer.explain_module_mark_lookup("CM2102", 120)
        with pytest.raises(ValueError, match="must not be blank"):
            explorer.explain_module_mark_lookup("   ", 50)
