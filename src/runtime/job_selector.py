from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time

from src.runtime.runtime_loader import RuntimePlanningData, normalize_runtime_string


WEEKDAY_NAME_TO_INDEX = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


@dataclass(frozen=True)
class RuntimeJob:
    article_title: str
    category: str
    cohort: str
    group_name: str
    day_of_week: str
    start_time: str
    end_time: str

    @property
    def matched_posting_window(self) -> str:
        return f"{self.day_of_week} {self.start_time}-{self.end_time}"


@dataclass(frozen=True)
class RuntimeJobSelectionDiagnostic:
    selected_job: RuntimeJob | None
    no_selection_reason: str | None


def select_runtime_job(
    runtime_planning: RuntimePlanningData, *, current_datetime: datetime
) -> RuntimeJob | None:
    return diagnose_runtime_job_selection(
        runtime_planning,
        current_datetime=current_datetime,
    ).selected_job


def diagnose_runtime_job_selection(
    runtime_planning: RuntimePlanningData, *, current_datetime: datetime
) -> RuntimeJobSelectionDiagnostic:
    open_windows = find_open_posting_windows(
        runtime_planning=runtime_planning,
        current_datetime=current_datetime,
    )
    if not open_windows:
        return RuntimeJobSelectionDiagnostic(
            selected_job=None,
            no_selection_reason="no_active_posting_windows",
        )

    eligible_jobs: list[RuntimeJob] = []
    category_rows_by_key = group_rows_by_key(
        runtime_planning.category_rows, key_name="category"
    )
    group_cohort_rows_by_key = group_rows_by_key(
        runtime_planning.group_cohort_rows, key_name="cohort"
    )
    category_match_found = False
    group_cohort_match_found = False

    for article_row in runtime_planning.article_rows:
        category_key = normalized_key(article_row["category"])
        for category_row in category_rows_by_key.get(category_key, ()):
            category_match_found = True
            cohort_key = normalized_key(category_row["cohort"])
            for group_row in group_cohort_rows_by_key.get(cohort_key, ()):
                group_cohort_match_found = True
                for window_row in open_windows.get(cohort_key, ()):
                    eligible_jobs.append(
                        RuntimeJob(
                            article_title=article_row["article_title"],
                            category=category_row["category"],
                            cohort=category_row["cohort"],
                            group_name=group_row["group_name"],
                            day_of_week=window_row["day_of_week"],
                            start_time=window_row["start_time"],
                            end_time=window_row["end_time"],
                        )
                    )

    if not eligible_jobs:
        if not category_match_found:
            no_selection_reason = "no_category_routing_match"
        elif not group_cohort_match_found:
            no_selection_reason = "no_group_cohort_match"
        else:
            no_selection_reason = "no_eligible_runtime_candidates"
        return RuntimeJobSelectionDiagnostic(
            selected_job=None,
            no_selection_reason=no_selection_reason,
        )

    return RuntimeJobSelectionDiagnostic(
        selected_job=sorted(
            eligible_jobs,
            key=lambda job: (
                normalized_key(job.article_title),
                normalized_key(job.category),
                normalized_key(job.cohort),
                normalized_key(job.group_name),
                normalized_key(job.day_of_week),
                job.start_time,
                job.end_time,
            ),
        )[0],
        no_selection_reason=None,
    )


def find_open_posting_windows(
    *, runtime_planning: RuntimePlanningData, current_datetime: datetime
) -> dict[str, tuple[dict[str, str], ...]]:
    current_weekday = current_datetime.weekday()
    current_time = current_datetime.time().replace(tzinfo=None)
    open_windows: dict[str, list[dict[str, str]]] = {}

    for window_row in runtime_planning.posting_window_rows:
        if weekday_name_to_index(window_row["day_of_week"]) != current_weekday:
            continue

        start_time = parse_runtime_time(window_row["start_time"])
        end_time = parse_runtime_time(window_row["end_time"])
        if not is_time_within_window(
            current_time=current_time,
            start_time=start_time,
            end_time=end_time,
        ):
            continue

        cohort_key = normalized_key(window_row["cohort"])
        open_windows.setdefault(cohort_key, []).append(window_row)

    return {
        cohort_key: tuple(
            sorted(
                rows,
                key=lambda row: (
                    normalized_key(row["day_of_week"]),
                    row["start_time"],
                    row["end_time"],
                ),
            )
        )
        for cohort_key, rows in open_windows.items()
    }


def group_rows_by_key(
    rows: tuple[dict[str, str], ...], *, key_name: str
) -> dict[str, tuple[dict[str, str], ...]]:
    grouped_rows: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped_rows.setdefault(normalized_key(row[key_name]), []).append(row)
    return {
        key: tuple(
            sorted(
                value,
                key=lambda row: tuple(
                    normalized_key(cell_value) for cell_value in row.values()
                ),
            )
        )
        for key, value in grouped_rows.items()
    }


def normalized_day_name(current_datetime: datetime) -> str:
    return weekday_index_to_name(current_datetime.weekday())


def normalized_key(value: str) -> str:
    return normalize_runtime_string(value).casefold()


def weekday_name_to_index(value: str) -> int:
    normalized_value = normalized_key(value)
    if normalized_value not in WEEKDAY_NAME_TO_INDEX:
        raise ValueError(f"Unsupported runtime day_of_week value: {value}")
    return WEEKDAY_NAME_TO_INDEX[normalized_value]


def weekday_index_to_name(value: int) -> str:
    for weekday_name, weekday_index in WEEKDAY_NAME_TO_INDEX.items():
        if weekday_index == value:
            return weekday_name
    raise ValueError(f"Unsupported weekday index: {value}")


def parse_runtime_time(value: str) -> time:
    return time.fromisoformat(value)


def is_time_within_window(
    *, current_time: time, start_time: time, end_time: time
) -> bool:
    return start_time <= current_time <= end_time
