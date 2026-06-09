"""Shared test scaffolding for the profile use cases.

The fake profile ports satisfy ``ProfileReader``, ``ProfileWriter``, and
``ActiveProfileWriter`` — the use cases never know about YAML, files, or
the resolver.
"""

from __future__ import annotations

import copy
from collections.abc import Callable, Iterator
from typing import Any

import pytest
from pydantic import BaseModel, SecretStr
from untaped import (
    get_settings,
    register_profile_settings,
)
from untaped.settings import reset_config_registry_for_tests


class _AwxTestSettings(BaseModel):
    base_url: str | None = None
    token: SecretStr | None = None


class _GithubTestSettings(BaseModel):
    token: SecretStr | None = None


@pytest.fixture(autouse=True)
def _register_secret_settings_for_redaction_tests() -> Iterator[None]:
    """Register small plugin schemas so profile-show redaction is testable."""
    reset_config_registry_for_tests()
    register_profile_settings("awx", _AwxTestSettings)
    register_profile_settings("github", _GithubTestSettings)
    get_settings.cache_clear()
    yield
    reset_config_registry_for_tests()
    get_settings.cache_clear()


class FakeProfilePorts:
    """In-memory fake satisfying the application port Protocols."""

    def __init__(
        self,
        profiles: dict[str, dict[str, Any]] | None = None,
        active: str | None = None,
        effective_active: str | None = None,
    ) -> None:
        self._profiles: dict[str, dict[str, Any]] = copy.deepcopy(profiles or {})
        self._persisted_active = active
        # Simulate a sticky env override (e.g. UNTAPED_PROFILE) — set_active
        # updates the persisted pointer but the override keeps winning, just
        # like the real ProfileFileRepository.
        self._effective_override = effective_active

    # ----- queries -----

    def names(self) -> list[str]:
        return list(self._profiles.keys())

    def active_name(self) -> str | None:
        return self._effective_override or self._persisted_active

    def persisted_active_name(self) -> str | None:
        return self._persisted_active

    def classify_active(self) -> tuple[str | None, str]:
        if self._effective_override:
            return self._effective_override, "env"
        if self._persisted_active:
            return self._persisted_active, "config"
        return None, "fallback"

    def read(self, name: str) -> dict[str, Any] | None:
        profile = self._profiles.get(name)
        return copy.deepcopy(profile) if profile is not None else None

    def resolved(self, name: str) -> dict[str, Any]:
        """Merge default ⤥ named, returning the effective dict."""
        merged: dict[str, Any] = {}
        for src_name in ("default", name):
            src = self._profiles.get(src_name)
            if not src:
                continue
            _deep_merge_into(merged, src)
        return merged

    # ----- mutations -----

    def write(self, name: str, data: dict[str, Any]) -> None:
        self._profiles[name] = copy.deepcopy(data)

    def delete(self, name: str) -> bool:
        return self._profiles.pop(name, None) is not None

    def rename(self, old: str, new: str) -> None:
        if old not in self._profiles:
            raise KeyError(old)
        if new in self._profiles:
            raise ValueError(new)
        self._profiles[new] = self._profiles.pop(old)
        if self._persisted_active == old:
            self._persisted_active = new

    def set_active(self, name: str) -> None:
        self._persisted_active = name


def _deep_merge_into(dst: dict[str, Any], src: dict[str, Any]) -> None:
    for key, value in src.items():
        if isinstance(value, dict):
            existing = dst.get(key)
            child = existing if isinstance(existing, dict) else {}
            dst[key] = child
            _deep_merge_into(child, value)
        else:
            dst[key] = value


@pytest.fixture
def repo() -> FakeProfilePorts:
    return FakeProfilePorts(
        profiles={
            "default": {"log_level": "INFO", "awx": {"api_prefix": "/api/v2/"}},
            "prod": {"awx": {"base_url": "https://prod"}},
            "stage": {"awx": {"base_url": "https://stage"}},
        },
        active="prod",
    )


@pytest.fixture
def empty_repo_factory() -> Callable[
    [dict[str, dict[str, Any]] | None, str | None, str | None],
    FakeProfilePorts,
]:
    """Return a callable that builds a fresh ``FakeProfilePorts`` with
    custom seed data — used by tests that need a different fixture shape."""

    def _make(
        profiles: dict[str, dict[str, Any]] | None = None,
        active: str | None = None,
        effective_active: str | None = None,
    ) -> FakeProfilePorts:
        return FakeProfilePorts(profiles=profiles, active=active, effective_active=effective_active)

    return _make
