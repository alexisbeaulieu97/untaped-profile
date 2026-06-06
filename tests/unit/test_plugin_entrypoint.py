"""Entry point and root-app integration checks for the profile plugin."""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from importlib.metadata import entry_points
from pathlib import Path

import pytest
from typer.testing import CliRunner
from untaped import get_settings
from untaped.main import build_app
from untaped.plugins import PluginRegistry

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


def test_profile_plugin_declares_untaped_api_version() -> None:
    assert profile_plugin.untaped_api_version == 1


def test_root_app_can_register_profile_plugin() -> None:
    app = build_app(plugins=[profile_plugin])

    result = CliRunner().invoke(app, ["profile", "--help"])

    assert result.exit_code == 0, result.output
    assert "Manage configuration profiles" in result.output


def test_profile_plugin_registers_agent_skill() -> None:
    registry = PluginRegistry()

    profile_plugin.register(registry)

    spec = registry.skills["untaped-profile"]
    assert spec.description == "Use the untaped profile plugin."
    assert spec.source.joinpath("SKILL.md").is_file()


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


def test_command_local_profile_flag_flows_into_profile_current(_isolate_config: Path) -> None:
    _isolate_config.write_text(
        "profiles:\n"
        "  default:\n    log_level: INFO\n"
        "  prod:\n    log_level: WARNING\n"
        "  stage:\n    log_level: DEBUG\n"
        "active: prod\n"
    )
    app = build_app(plugins=[profile_plugin])

    result = CliRunner().invoke(app, ["profile", "current", "--profile", "stage"])

    assert result.exit_code == 0, result.output
    assert result.stdout.splitlines() == ["stage"]
    assert "(source: env)" in result.stderr


def test_command_local_profile_flag_flows_into_profile_show(_isolate_config: Path) -> None:
    _isolate_config.write_text(
        "profiles:\n"
        "  default:\n    log_level: INFO\n"
        "  prod:\n    log_level: WARNING\n"
        "  stage:\n    log_level: DEBUG\n"
        "active: prod\n"
    )
    app = build_app(plugins=[profile_plugin])

    result = CliRunner().invoke(app, ["profile", "show", "--profile", "stage", "--format", "json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["name"] == "stage"
    assert payload["active"] is True
    assert payload["data"] == {"log_level": "DEBUG"}


def test_command_local_profile_flag_flows_into_profile_list(_isolate_config: Path) -> None:
    _isolate_config.write_text(
        "profiles:\n"
        "  default:\n    log_level: INFO\n"
        "  prod:\n    log_level: WARNING\n"
        "  stage:\n    log_level: DEBUG\n"
        "active: prod\n"
    )
    app = build_app(plugins=[profile_plugin])

    result = CliRunner().invoke(
        app,
        [
            "profile",
            "list",
            "--format",
            "raw",
            "--columns",
            "name",
            "--columns",
            "active",
            "--profile",
            "stage",
        ],
    )

    assert result.exit_code == 0, result.output
    rows = {line.split("\t")[0]: line.split("\t")[1] for line in result.stdout.splitlines()}
    assert rows["stage"] == "✓"
    assert rows["prod"] == ""


@pytest.mark.parametrize(
    "args",
    [
        ["profile", "use", "stage", "--profile", "prod"],
        ["profile", "delete", "stage", "--profile", "prod"],
        ["profile", "rename", "stage", "qa", "--profile", "prod"],
    ],
)
def test_command_local_profile_flag_is_not_registered_on_mutations(
    _isolate_config: Path,
    args: list[str],
) -> None:
    _isolate_config.write_text(
        "profiles:\n"
        "  default:\n    log_level: INFO\n"
        "  prod:\n    log_level: WARNING\n"
        "  stage:\n    log_level: DEBUG\n"
        "active: prod\n"
    )
    app = build_app(plugins=[profile_plugin])

    result = CliRunner().invoke(app, args)

    assert result.exit_code != 0
    assert "No such option: --profile" in result.output
