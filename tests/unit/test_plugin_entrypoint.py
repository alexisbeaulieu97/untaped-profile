"""Entry point and root-app integration checks for the profile plugin."""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from importlib.metadata import entry_points
from pathlib import Path

import pytest
from untaped import get_settings
from untaped.api import CliSpec, PluginManifest, PluginRegistry
from untaped.main import build_app
from untaped.plugins import register_plugins
from untaped.testing import CliInvoker

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
    assert profile_plugin.untaped_api_version == 3


def test_profile_plugin_manifest_shape() -> None:
    manifest = profile_plugin.manifest()

    assert isinstance(manifest, PluginManifest)
    cli_spec = manifest.clis[0]
    assert isinstance(cli_spec, CliSpec)
    assert cli_spec.name == "profile"
    assert cli_spec.app is None
    assert cli_spec.import_path == "untaped_profile.cli:app"
    assert cli_spec.help
    assert [skill.name for skill in manifest.skills] == ["untaped-profile"]
    assert not manifest.profile_settings
    assert not manifest.state_settings
    assert not manifest.themes
    assert not manifest.diagnostics


def test_root_app_can_register_profile_plugin() -> None:
    app = build_app(plugins=[profile_plugin])

    result = CliInvoker().invoke(app, ["profile", "--help"])

    assert result.exit_code == 0, result.output
    assert "Manage configuration profiles" in result.output


def test_profile_plugin_registers_agent_skill() -> None:
    registry = PluginRegistry()

    register_plugins(registry, [profile_plugin])

    assert registry.load_errors == []
    spec = registry.skills["untaped-profile"]
    assert spec.description == "Use the untaped profile plugin."
    assert spec.source.joinpath("SKILL.md").is_file()
    assert "profile" in registry.lazy_clis


def test_root_profile_flag_flows_into_profile_current(_isolate_config: Path) -> None:
    _isolate_config.write_text(
        "profiles:\n"
        "  default:\n    log_level: INFO\n"
        "  prod:\n    log_level: WARNING\n"
        "  stage:\n    log_level: DEBUG\n"
        "active: prod\n"
    )
    app = build_app(plugins=[profile_plugin])

    result = CliInvoker().invoke(app, ["--profile", "stage", "profile", "current"])

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

    result = CliInvoker().invoke(app, ["profile", "current", "--profile", "stage"])

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

    result = CliInvoker().invoke(app, ["profile", "show", "--profile", "stage", "--format", "json"])

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

    result = CliInvoker().invoke(
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


def test_root_profile_flag_is_available_on_profile_mutations(_isolate_config: Path) -> None:
    _isolate_config.write_text(
        "profiles:\n"
        "  default:\n    log_level: INFO\n"
        "  prod:\n    log_level: WARNING\n"
        "  stage:\n    log_level: DEBUG\n"
        "active: prod\n"
    )
    app = build_app(plugins=[profile_plugin])

    # The root --profile flag must precede the command; mutating commands do
    # not expose a command-local --profile selector.
    result = CliInvoker().invoke(app, ["--profile", "prod", "profile", "use", "stage"])

    assert result.exit_code == 0, result.output
    assert "active profile: stage" in result.output
