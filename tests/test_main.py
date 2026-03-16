from __future__ import annotations

from src.core.config import Settings
from src.main import load_group_targets_file, resolve_group_targets


def test_load_group_targets_file_ignores_blank_lines(tmp_path) -> None:
    group_targets_file = tmp_path / "group_targets.txt"
    group_targets_file.write_text("\nGrupo Uno\n\nGrupo Dos\n", encoding="utf-8")

    targets = load_group_targets_file(group_targets_file)

    assert targets == ["Grupo Uno", "Grupo Dos"]


def test_resolve_group_targets_falls_back_to_single_group_when_file_missing(
    tmp_path,
) -> None:
    settings = Settings(
        base_url="https://example.com",
        marketplace_group_targets_file=tmp_path / "missing.txt",
        marketplace_group_name="Grupo Fallback",
    )

    targets = resolve_group_targets(settings)

    assert targets == ["Grupo Fallback"]
