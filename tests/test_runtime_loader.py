from __future__ import annotations

import pytest

from src.core.config import Settings
from src.runtime.runtime_loader import (
    RuntimePlanningError,
    load_runtime_planning,
    normalize_runtime_string,
)


def test_load_runtime_planning_reads_and_summarizes_runtime_files(tmp_path) -> None:
    article_file = tmp_path / "article_routing.csv"
    article_file.write_text(
        "article_title,category\n"
        " Enchufe Inteligente Wi-Fi  , Smart Home \n",
        encoding="utf-8",
    )
    category_file = tmp_path / "category_routing.csv"
    category_file.write_text(
        "category,cohort\n"
        " Smart Home , Evening Groups \n",
        encoding="utf-8",
    )
    group_cohorts_file = tmp_path / "group_cohorts.csv"
    group_cohorts_file.write_text(
        "group_name,cohort\n"
        "Las Piedras, Evening Groups\n",
        encoding="utf-8",
    )
    posting_windows_file = tmp_path / "posting_windows.csv"
    posting_windows_file.write_text(
        "cohort,day_of_week,start_time,end_time\n"
        "Evening Groups,monday,18:00,20:00\n",
        encoding="utf-8",
    )

    settings = Settings(
        runtime_article_routing_file=article_file,
        runtime_category_routing_file=category_file,
        runtime_group_cohorts_file=group_cohorts_file,
        runtime_posting_windows_file=posting_windows_file,
    )

    runtime_planning = load_runtime_planning(settings)

    assert runtime_planning.article_count == 1
    assert runtime_planning.categories == ("smart home",)
    assert runtime_planning.cohorts == ("evening groups",)
    assert runtime_planning.posting_window_count == 1
    assert runtime_planning.article_rows[0]["article_title"] == "Enchufe Inteligente Wi-Fi"


def test_load_runtime_planning_fails_with_helpful_missing_column_error(
    tmp_path,
) -> None:
    article_file = tmp_path / "article_routing.csv"
    article_file.write_text("article_title\nEnchufe\n", encoding="utf-8")
    category_file = tmp_path / "category_routing.csv"
    category_file.write_text("category,cohort\nSmart Home,Evening\n", encoding="utf-8")
    group_cohorts_file = tmp_path / "group_cohorts.csv"
    group_cohorts_file.write_text("group_name,cohort\nGrupo Uno,Evening\n", encoding="utf-8")
    posting_windows_file = tmp_path / "posting_windows.csv"
    posting_windows_file.write_text(
        "cohort,day_of_week,start_time,end_time\nEvening,monday,18:00,20:00\n",
        encoding="utf-8",
    )

    settings = Settings(
        runtime_article_routing_file=article_file,
        runtime_category_routing_file=category_file,
        runtime_group_cohorts_file=group_cohorts_file,
        runtime_posting_windows_file=posting_windows_file,
    )

    with pytest.raises(RuntimePlanningError, match="missing required columns"):
        load_runtime_planning(settings)


def test_normalize_runtime_string_collapses_whitespace() -> None:
    assert normalize_runtime_string("  Smart   Home  ") == "Smart Home"
