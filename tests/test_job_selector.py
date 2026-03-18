from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from src.runtime.job_selector import diagnose_runtime_job_selection, select_runtime_job
from src.runtime.runtime_loader import RuntimePlanningData


def test_select_runtime_job_matches_open_posting_window() -> None:
    runtime_planning = RuntimePlanningData(
        article_rows=(
            {"article_title": "Smart Plug", "category": "Smart Home"},
        ),
        category_rows=(
            {"category": "Smart Home", "cohort": "Evening Groups"},
        ),
        group_cohort_rows=(
            {"group_name": "Group One", "cohort": "Evening Groups"},
        ),
        posting_window_rows=(
            {
                "cohort": "Evening Groups",
                "day_of_week": "monday",
                "start_time": "18:00",
                "end_time": "20:00",
            },
        ),
    )

    selected_job = select_runtime_job(
        runtime_planning,
        current_datetime=datetime(2026, 3, 16, 18, 30),
    )

    assert selected_job is not None
    assert selected_job.article_title == "Smart Plug"
    assert selected_job.category == "Smart Home"
    assert selected_job.cohort == "Evening Groups"
    assert selected_job.group_name == "Group One"
    assert selected_job.matched_posting_window == "monday 18:00-20:00"


def test_select_runtime_job_returns_none_when_no_window_is_open() -> None:
    runtime_planning = RuntimePlanningData(
        article_rows=(
            {"article_title": "Smart Plug", "category": "Smart Home"},
        ),
        category_rows=(
            {"category": "Smart Home", "cohort": "Evening Groups"},
        ),
        group_cohort_rows=(
            {"group_name": "Group One", "cohort": "Evening Groups"},
        ),
        posting_window_rows=(
            {
                "cohort": "Evening Groups",
                "day_of_week": "monday",
                "start_time": "18:00",
                "end_time": "20:00",
            },
        ),
    )

    selected_job = select_runtime_job(
        runtime_planning,
        current_datetime=datetime(2026, 3, 16, 17, 59),
    )

    assert selected_job is None


def test_select_runtime_job_uses_deterministic_sorted_order() -> None:
    runtime_planning = RuntimePlanningData(
        article_rows=(
            {"article_title": "Zulu Lamp", "category": "Decor"},
            {"article_title": "Alpha Lamp", "category": "Decor"},
        ),
        category_rows=(
            {"category": "Decor", "cohort": "Evening Groups"},
        ),
        group_cohort_rows=(
            {"group_name": "Group B", "cohort": "Evening Groups"},
            {"group_name": "Group A", "cohort": "Evening Groups"},
        ),
        posting_window_rows=(
            {
                "cohort": "Evening Groups",
                "day_of_week": "monday",
                "start_time": "18:00",
                "end_time": "20:00",
            },
        ),
    )

    selected_job = select_runtime_job(
        runtime_planning,
        current_datetime=datetime(2026, 3, 16, 18, 30),
    )

    assert selected_job is not None
    assert selected_job.article_title == "Alpha Lamp"
    assert selected_job.group_name == "Group A"


def test_select_runtime_job_matches_weekday_without_locale_day_name_dependency() -> None:
    runtime_planning = RuntimePlanningData(
        article_rows=(
            {"article_title": "Mate Set", "category": "Kitchen"},
        ),
        category_rows=(
            {"category": "Kitchen", "cohort": "Weekend Groups"},
        ),
        group_cohort_rows=(
            {"group_name": "Group Montevideo", "cohort": "Weekend Groups"},
        ),
        posting_window_rows=(
            {
                "cohort": "Weekend Groups",
                "day_of_week": "  SUNDAY ",
                "start_time": "09:00",
                "end_time": "11:00",
            },
        ),
    )

    selected_job = select_runtime_job(
        runtime_planning,
        current_datetime=datetime(2026, 3, 22, 10, 0, tzinfo=ZoneInfo("UTC")),
    )

    assert selected_job is not None
    assert selected_job.day_of_week.strip() == "SUNDAY"


def test_diagnose_runtime_job_selection_reports_no_active_posting_windows() -> None:
    runtime_planning = RuntimePlanningData(
        article_rows=(
            {"article_title": "Smart Plug", "category": "Smart Home"},
        ),
        category_rows=(
            {"category": "Smart Home", "cohort": "Evening Groups"},
        ),
        group_cohort_rows=(
            {"group_name": "Group One", "cohort": "Evening Groups"},
        ),
        posting_window_rows=(
            {
                "cohort": "Evening Groups",
                "day_of_week": "monday",
                "start_time": "18:00",
                "end_time": "20:00",
            },
        ),
    )

    diagnostic = diagnose_runtime_job_selection(
        runtime_planning,
        current_datetime=datetime(2026, 3, 16, 17, 59),
    )

    assert diagnostic.selected_job is None
    assert diagnostic.no_selection_reason == "no_active_posting_windows"


def test_diagnose_runtime_job_selection_reports_no_category_routing_match() -> None:
    runtime_planning = RuntimePlanningData(
        article_rows=(
            {"article_title": "Smart Plug", "category": "Smart Home"},
        ),
        category_rows=(
            {"category": "Decor", "cohort": "Evening Groups"},
        ),
        group_cohort_rows=(
            {"group_name": "Group One", "cohort": "Evening Groups"},
        ),
        posting_window_rows=(
            {
                "cohort": "Evening Groups",
                "day_of_week": "monday",
                "start_time": "18:00",
                "end_time": "20:00",
            },
        ),
    )

    diagnostic = diagnose_runtime_job_selection(
        runtime_planning,
        current_datetime=datetime(2026, 3, 16, 18, 30),
    )

    assert diagnostic.selected_job is None
    assert diagnostic.no_selection_reason == "no_category_routing_match"


def test_diagnose_runtime_job_selection_reports_no_group_cohort_match() -> None:
    runtime_planning = RuntimePlanningData(
        article_rows=(
            {"article_title": "Smart Plug", "category": "Smart Home"},
        ),
        category_rows=(
            {"category": "Smart Home", "cohort": "Evening Groups"},
        ),
        group_cohort_rows=(
            {"group_name": "Group One", "cohort": "Morning Groups"},
        ),
        posting_window_rows=(
            {
                "cohort": "Evening Groups",
                "day_of_week": "monday",
                "start_time": "18:00",
                "end_time": "20:00",
            },
        ),
    )

    diagnostic = diagnose_runtime_job_selection(
        runtime_planning,
        current_datetime=datetime(2026, 3, 16, 18, 30),
    )

    assert diagnostic.selected_job is None
    assert diagnostic.no_selection_reason == "no_group_cohort_match"


def test_diagnose_runtime_job_selection_reports_no_eligible_runtime_candidates() -> None:
    runtime_planning = RuntimePlanningData(
        article_rows=(
            {"article_title": "Smart Plug", "category": "Smart Home"},
        ),
        category_rows=(
            {"category": "Smart Home", "cohort": "Evening Groups"},
        ),
        group_cohort_rows=(
            {"group_name": "Group One", "cohort": "Evening Groups"},
        ),
        posting_window_rows=(
            {
                "cohort": "Morning Groups",
                "day_of_week": "monday",
                "start_time": "09:00",
                "end_time": "11:00",
            },
        ),
    )

    diagnostic = diagnose_runtime_job_selection(
        runtime_planning,
        current_datetime=datetime(2026, 3, 16, 9, 30),
    )

    assert diagnostic.selected_job is None
    assert diagnostic.no_selection_reason == "no_eligible_runtime_candidates"
