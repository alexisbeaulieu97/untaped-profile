"""The settings layout this plugin contributes to core.

Maps the raw config dict to effective settings by layering
``profiles.default`` beneath ``profiles.<active>``. Core resolves
``LAYOUT`` lazily (via ``SettingsLayoutSpec`` in the plugin manifest) the
first time settings are read.
"""

from __future__ import annotations

from typing import Any

from untaped.api import ConfigError

from untaped_profile.domain.resolver import (
    DEFAULT_PROFILE,
    effective_active_profile_name,
    resolve_profiles,
)


class ProfilesSettingsLayout:
    """``untaped.settings_layout.SettingsLayout`` implementation for profiles."""

    supports_scopes = True

    def effective(self, raw: dict[str, Any], *, scope: str | None = None) -> dict[str, Any]:
        effective, _ = self._resolve(raw, scope)
        return effective

    def provenance(self, raw: dict[str, Any]) -> dict[tuple[str, ...], str]:
        _, provenance = self._resolve(raw)
        return provenance

    def _resolve(
        self, raw: dict[str, Any], scope: str | None = None
    ) -> tuple[dict[str, Any], dict[tuple[str, ...], str]]:
        """Resolve effective settings + provenance for the active (or given) scope."""
        override = scope or effective_active_profile_name(raw)
        return resolve_profiles(raw, active_override=override)

    def scope_names(self, raw: dict[str, Any]) -> list[str]:
        profiles = raw.get("profiles")
        return sorted(profiles) if isinstance(profiles, dict) else []

    def scope_data(self, raw: dict[str, Any], name: str) -> dict[str, Any] | None:
        profiles = raw.get("profiles")
        if not isinstance(profiles, dict):
            return None
        data = profiles.get(name)
        return data if isinstance(data, dict) else None

    def write_scope(self, raw: dict[str, Any], requested: str | None) -> tuple[dict[str, Any], str]:
        """Return the target profile's dict, creating only ``default``.

        Any other target must already exist — this is the guardrail that
        keeps ``config set --target-profile typo`` from silently creating a
        new profile.
        """
        name = requested or effective_active_profile_name(raw) or DEFAULT_PROFILE
        existing = raw.get("profiles")
        known = existing if isinstance(existing, dict) else {}
        if name != DEFAULT_PROFILE and name not in known:
            known_str = ", ".join(sorted(known)) or "(none)"
            raise ConfigError(
                f"profile {name!r} does not exist; known profiles: {known_str}. "
                "Create it first with `untaped profile create`."
            )
        profiles = raw.setdefault("profiles", {})
        if not isinstance(profiles, dict):
            raise ConfigError("config key 'profiles' must be a mapping")
        target = profiles.setdefault(name, {})
        if not isinstance(target, dict):
            raise ConfigError(f"profile {name!r} must be a mapping")
        return target, name


LAYOUT = ProfilesSettingsLayout()
