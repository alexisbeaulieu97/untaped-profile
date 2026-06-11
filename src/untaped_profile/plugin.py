"""Untaped plugin registration for profile management commands."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from untaped.api import CliSpec, PluginManifest, SkillSpec


class ProfilePlugin:
    id = "profile"
    untaped_api_version = 3

    def manifest(self) -> PluginManifest:
        return PluginManifest(
            clis=(
                CliSpec(
                    name="profile",
                    import_path="untaped_profile.cli:app",
                    help="Manage configuration profiles in ``~/.untaped/config.yml``.",
                ),
            ),
            skills=(
                SkillSpec(
                    name="untaped-profile",
                    source=Path(
                        str(files("untaped_profile").joinpath("skills", "untaped-profile"))
                    ),
                    description="Use the untaped profile plugin.",
                ),
            ),
        )


plugin = ProfilePlugin()
