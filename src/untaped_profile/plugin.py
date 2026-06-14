"""Untaped plugin registration for profile management commands."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from untaped.api import (
    CliSpec,
    PluginManifest,
    RootOptionSpec,
    SettingsLayoutSpec,
    SkillSpec,
)

PROFILE_OPTION_HELP = (
    "Override the active profile for this invocation only "
    "(equivalent to setting the UNTAPED_PROFILE environment variable)."
)


class ProfilePlugin:
    id = "profile"
    untaped_api_version = 5

    def manifest(self) -> PluginManifest:
        return PluginManifest(
            clis=(
                CliSpec(
                    name="profile",
                    import_path="untaped_profile.cli:app",
                    help="Manage configuration profiles in ``~/.untaped/config.yml``.",
                ),
            ),
            root_options=(
                RootOptionSpec(
                    name="--profile",
                    help=PROFILE_OPTION_HELP,
                    handler_import_path="untaped_profile.root_option:apply",
                ),
            ),
            settings_layout=SettingsLayoutSpec(import_path="untaped_profile.layout:LAYOUT"),
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
