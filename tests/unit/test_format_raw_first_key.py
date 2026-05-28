"""Pin the ``profile list --format raw`` first-key contract."""

from __future__ import annotations

import ast
from collections.abc import Callable
from pathlib import Path

import pytest

from untaped_profile.cli.commands import _profile_row
from untaped_profile.domain.models import Profile

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("label", "factory", "expected_first_key"),
    [
        (
            "untaped_profile.cli.commands._profile_row",
            lambda: _profile_row(Profile(name="default", data={}, is_active=True)),
            "name",
        )
    ],
)
def test_hand_built_row_first_key(
    label: str,
    factory: Callable[[], dict[str, object]],
    expected_first_key: str,
) -> None:
    row = factory()
    actual = next(iter(row.keys()))

    assert actual == expected_first_key, (
        f"{label}'s first key is {actual!r}; expected {expected_first_key!r}."
    )


def test_profile_list_command_calls_profile_row_helper() -> None:
    source = REPO_ROOT / "src/untaped_profile/cli/commands.py"
    tree = ast.parse(source.read_text())

    calls: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "list_command":
            calls = {
                sub.func.id
                for sub in ast.walk(node)
                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name)
            }
            break

    assert "_profile_row" in calls
