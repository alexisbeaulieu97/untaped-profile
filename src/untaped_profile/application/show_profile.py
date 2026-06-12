"""Use case: render a single profile's contents (effective or raw)."""

from __future__ import annotations

from untaped.api import ConfigError

from untaped_profile.application.ports import ProfileReader
from untaped_profile.domain import Profile
from untaped_profile.domain.resolver import DEFAULT_PROFILE


class ShowProfile:
    """Return the named profile.

    By default the data is the **effective view**: ``default`` merged with
    the named profile (named wins per leaf). ``raw=True`` returns only
    what's literally written under ``profiles.<name>``.
    """

    def __init__(self, repo: ProfileReader) -> None:
        self._repo = repo

    def __call__(
        self,
        name: str,
        *,
        raw: bool = False,
        allow_conceptual_default: bool = False,
    ) -> Profile:
        raw_data = self._repo.read(name)
        if raw_data is None and name == DEFAULT_PROFILE and allow_conceptual_default:
            data = {} if raw else self._repo.resolved(name)
            active = self._repo.active_name() or DEFAULT_PROFILE
            return Profile(name=name, data=data, is_active=(name == active))
        if raw_data is None:
            known = ", ".join(sorted(self._repo.names())) or "(none)"
            raise ConfigError(f"profile {name!r} does not exist. Known: {known}")
        data = raw_data if raw else self._repo.resolved(name)
        active = self._repo.active_name() or DEFAULT_PROFILE
        return Profile(name=name, data=data, is_active=(name == active))
