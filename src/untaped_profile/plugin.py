"""Untaped plugin registration for profile management commands."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from untaped.plugins import PluginRegistry, SkillSpec

from untaped_profile import app


class ProfilePlugin:
    id = "profile"
    untaped_api_version = 2

    def register(self, registry: PluginRegistry) -> None:
        registry.add_cli("profile", app)
        registry.add_skill(
            SkillSpec(
                name="untaped-profile",
                source=Path(str(files("untaped_profile").joinpath("skills", "untaped-profile"))),
                description="Use the untaped profile plugin.",
            )
        )


plugin = ProfilePlugin()
