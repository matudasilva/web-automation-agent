from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.core.config import Settings


class RuntimePlanningError(ValueError):
    pass


@dataclass(frozen=True)
class RuntimePlanningData:
    article_rows: tuple[dict[str, str], ...]
    category_rows: tuple[dict[str, str], ...]
    group_cohort_rows: tuple[dict[str, str], ...]
    posting_window_rows: tuple[dict[str, str], ...]

    @property
    def article_count(self) -> int:
        return len(self.article_rows)

    @property
    def categories(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    normalize_runtime_string(row["category"]).casefold()
                    for row in self.article_rows + self.category_rows
                }
            )
        )

    @property
    def cohorts(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    normalize_runtime_string(row["cohort"]).casefold()
                    for row in self.category_rows
                    + self.group_cohort_rows
                    + self.posting_window_rows
                }
            )
        )

    @property
    def posting_window_count(self) -> int:
        return len(self.posting_window_rows)


RUNTIME_FILE_SPECS = {
    "article_routing": ("article_title", "category"),
    "category_routing": ("category", "cohort"),
    "group_cohorts": ("group_name", "cohort"),
    "posting_windows": ("cohort", "day_of_week", "start_time", "end_time"),
}


def load_runtime_planning(settings: Settings) -> RuntimePlanningData:
    article_rows = load_runtime_csv(
        file_path=settings.runtime_article_routing_file,
        required_columns=RUNTIME_FILE_SPECS["article_routing"],
    )
    category_rows = load_runtime_csv(
        file_path=settings.runtime_category_routing_file,
        required_columns=RUNTIME_FILE_SPECS["category_routing"],
    )
    group_cohort_rows = load_runtime_csv(
        file_path=settings.runtime_group_cohorts_file,
        required_columns=RUNTIME_FILE_SPECS["group_cohorts"],
    )
    posting_window_rows = load_runtime_csv(
        file_path=settings.runtime_posting_windows_file,
        required_columns=RUNTIME_FILE_SPECS["posting_windows"],
    )
    return RuntimePlanningData(
        article_rows=tuple(article_rows),
        category_rows=tuple(category_rows),
        group_cohort_rows=tuple(group_cohort_rows),
        posting_window_rows=tuple(posting_window_rows),
    )


def load_runtime_csv(
    *, file_path: Path, required_columns: tuple[str, ...]
) -> list[dict[str, str]]:
    if not file_path.exists():
        raise RuntimePlanningError(
            f"Runtime planning file '{file_path}' does not exist"
        )

    with file_path.open("r", encoding="utf-8", newline="") as file_handle:
        reader = csv.DictReader(file_handle)
        if reader.fieldnames is None:
            raise RuntimePlanningError(
                f"Runtime planning file '{file_path}' is missing a header row"
            )

        normalized_fieldnames = [normalize_runtime_string(name) for name in reader.fieldnames]
        missing_columns = [
            column for column in required_columns if column not in normalized_fieldnames
        ]
        if missing_columns:
            raise RuntimePlanningError(
                f"Runtime planning file '{file_path}' is missing required columns "
                f"{missing_columns}. Found columns: {normalized_fieldnames}"
            )

        rows: list[dict[str, str]] = []
        for row_index, raw_row in enumerate(reader, start=2):
            normalized_row = {
                normalize_runtime_string(key): normalize_runtime_string(value)
                for key, value in raw_row.items()
                if key is not None
            }
            for required_column in required_columns:
                if not normalized_row.get(required_column):
                    raise RuntimePlanningError(
                        f"Runtime planning file '{file_path}' has an empty required value "
                        f"for column '{required_column}' on row {row_index}"
                    )
            rows.append(normalized_row)
        return rows


def normalize_runtime_string(value: str | None) -> str:
    if value is None:
        return ""
    return " ".join(value.strip().split())
