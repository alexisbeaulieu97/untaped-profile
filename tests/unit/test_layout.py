"""Tests for the settings layout this plugin contributes to core."""

from __future__ import annotations

import pytest
from untaped.api import ConfigError
from untaped.settings_layout import SettingsLayout

from untaped_profile.layout import LAYOUT, ProfilesSettingsLayout

RAW = {
    "profiles": {
        "default": {"log_level": "WARNING", "http": {"verify_ssl": False}},
        "stage": {"log_level": "DEBUG"},
    },
    "active": "stage",
}


def test_module_layout_satisfies_core_protocol() -> None:
    assert isinstance(LAYOUT, SettingsLayout)
    assert LAYOUT.supports_scopes is True


def test_effective_layers_default_beneath_active() -> None:
    effective = ProfilesSettingsLayout().effective(dict(RAW))
    assert effective["log_level"] == "DEBUG"
    assert effective["http"] == {"verify_ssl": False}


def test_effective_honours_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("UNTAPED_PROFILE", "default")
    effective = ProfilesSettingsLayout().effective(dict(RAW))
    assert effective["log_level"] == "WARNING"


def test_effective_rejects_undefined_active_profile() -> None:
    raw = {"profiles": {"default": {}}, "active": "nope"}
    with pytest.raises(ConfigError, match="nope"):
        ProfilesSettingsLayout().effective(raw)


def test_provenance_names_supplying_profile() -> None:
    provenance = ProfilesSettingsLayout().provenance(dict(RAW))
    assert provenance[("log_level",)] == "stage"
    assert provenance[("http", "verify_ssl")] == "default"


def test_scope_names_and_data() -> None:
    layout = ProfilesSettingsLayout()
    assert layout.scope_names(dict(RAW)) == ["default", "stage"]
    assert layout.scope_data(dict(RAW), "stage") == {"log_level": "DEBUG"}
    assert layout.scope_data(dict(RAW), "missing") is None
    assert layout.scope_names({}) == []


def test_write_scope_targets_requested_existing_profile() -> None:
    raw: dict[str, object] = {"profiles": {"prod": {}}}
    target, name = ProfilesSettingsLayout().write_scope(raw, "prod")
    target["log_level"] = "ERROR"
    assert name == "prod"
    assert raw == {"profiles": {"prod": {"log_level": "ERROR"}}}


def test_write_scope_rejects_unknown_requested_profile() -> None:
    with pytest.raises(ConfigError, match="does not exist"):
        ProfilesSettingsLayout().write_scope({"profiles": {"prod": {}}}, "typo")


def test_write_scope_defaults_to_active_then_default() -> None:
    layout = ProfilesSettingsLayout()
    raw_active: dict[str, object] = {"active": "prod", "profiles": {"prod": {}}}
    _, name = layout.write_scope(raw_active, None)
    assert name == "prod"
    # `default` is the auto-created floor: allowed even when missing.
    raw_empty: dict[str, object] = {}
    _, fallback = layout.write_scope(raw_empty, None)
    assert fallback == "default"
    assert raw_empty == {"profiles": {"default": {}}}


def test_effective_with_explicit_scope_overrides_active() -> None:
    effective = ProfilesSettingsLayout().effective(dict(RAW), scope="default")
    assert effective["log_level"] == "WARNING"
