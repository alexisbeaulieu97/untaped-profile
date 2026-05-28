"""Entry point and root-app integration checks for the profile plugin."""

from __future__ import annotations

import os
from collections.abc import Iterator
from importlib.metadata import entry_points
from pathlib import Path

import pytest
from typer.testing import CliRunner
from untaped import get_settings
from untaped.main import build_app

from untaped_profile.plugin import plugin as profile_plugin


@pytest.fixture(autouse=True)
def _isolate_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    cfg = tmp_path / "config.yml"
    monkeypatch.setenv("UNTAPED_CONFIG", str(cfg))
    monkeypatch.delenv("UNTAPED_PROFILE", raising=False)
    get_settings.cache_clear()
    yield cfg
    os.environ.pop("UNTAPED_PROFILE", None)
    get_settings.cache_clear()


def test_profile_plugin_entry_point_is_declared() -> None:
    matches = [
        ep
        for ep in entry_points(group="untaped.plugins")
        if ep.name == "profile" and ep.value == "untaped_profile.plugin:plugin"
    ]

    assert matches


def test_root_app_can_register_profile_plugin() -> None:
    app = build_app(plugins=[profile_plugin])

    result = CliRunner().invoke(app, ["profile", "--help"])

    assert result.exit_code == 0, result.output
    assert "Manage configuration profiles" in result.output


def test_root_profile_flag_flows_into_profile_current(_isolate_config: Path) -> None:
    _isolate_config.write_text(
        "profiles:\n"
        "  default:\n    log_level: INFO\n"
        "  prod:\n    log_level: WARNING\n"
        "  stage:\n    log_level: DEBUG\n"
        "active: prod\n"
    )
    app = build_app(plugins=[profile_plugin])

    result = CliRunner().invoke(app, ["--profile", "stage", "profile", "current"])

    assert result.exit_code == 0, result.output
    assert result.stdout.splitlines() == ["stage"]
    assert "(source: env)" in result.stderr
