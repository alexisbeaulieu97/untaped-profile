"""Use case: delete a profile (refusing destructive cases)."""

from __future__ import annotations

from untaped.api import ConfigError

from untaped_profile.application.ports import ProfileWriter
from untaped_profile.domain.models import ProfileDeletePreview


class DeleteProfile:
    """Remove ``profiles.<name>``.

    Refuses to delete the active profile (would orphan the ``active:``
    pointer). ``default`` is not special-cased — when it's not the
    active profile, deleting it just clears any shared overrides and
    values fall through to schema defaults.
    """

    def __init__(self, repo: ProfileWriter) -> None:
        self._repo = repo

    def preview(self, name: str) -> ProfileDeletePreview:
        data = self._repo.read(name)
        if data is None:
            known = ", ".join(sorted(self._repo.names())) or "(none)"
            raise ConfigError(f"profile {name!r} does not exist. Known: {known}")
        if self._repo.persisted_active_name() == name:
            raise ConfigError(
                f"cannot delete the active profile {name!r}; "
                "switch to another profile first with `untaped profile use`"
            )
        return ProfileDeletePreview(name=name, top_level_keys=tuple(sorted(data)))

    def __call__(self, name: str) -> None:
        self.preview(name)
        self._repo.delete(name)
