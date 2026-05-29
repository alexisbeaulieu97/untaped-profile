"""Typer commands: ``untaped profile list / show / use / current / create / delete / rename``."""

from __future__ import annotations

import json
import sys
from typing import Literal

import typer
import yaml
from untaped import (
    ColumnsOption,
    ConfigError,
    FormatOption,
    ProfileOverrideOption,
    format_output,
    get_profile_settings_model,
    profile_override,
    redact_secrets,
    report_errors,
    resolve_config_path,
    secret_field_paths,
)

from untaped_profile.application import (
    CreateProfile,
    CurrentProfile,
    DeleteProfile,
    ListProfiles,
    RenameProfile,
    ShowProfile,
    UseProfile,
)
from untaped_profile.domain.models import Profile, ProfileDeletePreview
from untaped_profile.infrastructure import ProfileFileRepository

# `profile show` returns a single nested object — `raw`/`table` (which want
# tabular rows) don't apply, so narrow the format type for this command and
# let Typer reject other values at parse time.
ShowFormat = Literal["yaml", "json"]

app = typer.Typer(
    name="profile",
    help="Manage configuration profiles in ``~/.untaped/config.yml``.",
    no_args_is_help=True,
)


@app.callback()
def _callback() -> None:
    """Manage configuration profiles in ``~/.untaped/config.yml``."""


@app.command("list")
def list_command(
    fmt: FormatOption = "table",
    columns: ColumnsOption = None,
    profile: ProfileOverrideOption = None,
) -> None:
    """List every profile, marking which one is active."""
    with report_errors(), profile_override(profile):
        profiles = ListProfiles(ProfileFileRepository())()
        rows: list[dict[str, object]] = [_profile_row(p) for p in profiles]
        typer.echo(format_output(rows, fmt=fmt, columns=columns))


@app.command("show")
def show_command(
    name: str | None = typer.Argument(
        None, help="Profile name to inspect; defaults to the current profile."
    ),
    raw: bool = typer.Option(
        False,
        "--raw",
        help="Show only the keys this profile literally sets (no `default` fallback merge).",
    ),
    show_secrets: bool = typer.Option(
        False,
        "--show-secrets",
        help="Reveal secret values instead of `***`.",
    ),
    fmt: ShowFormat = typer.Option(
        "yaml",
        "--format",
        "-f",
        help="Output format (yaml or json).",
    ),
    profile: ProfileOverrideOption = None,
) -> None:
    """Print a profile's contents (effective view by default).

    ``yaml`` (default) prints the merged data as a flat YAML document for
    human use; ``json`` emits a wrapped envelope so downstream tools can
    address the metadata fields (``jq '.data.awx.base_url'`` etc.).
    ``raw`` and ``table`` are not supported — a single nested object has
    no rows for those formats to render.

    Secrets (AWX/GitHub tokens) are masked as ``***`` in both formats
    unless ``--show-secrets`` is passed, mirroring ``untaped config list``.
    """
    with report_errors(), profile_override(profile):
        repo = ProfileFileRepository()
        if name is None:
            current = CurrentProfile(repo)()
            target = current.name
            allow_conceptual_default = current.source == "fallback"
        else:
            target = name
            allow_conceptual_default = False
        target_profile = ShowProfile(repo)(
            target,
            raw=raw,
            allow_conceptual_default=allow_conceptual_default,
        )
        header = f"# profile: {target_profile.name}"
        if target_profile.is_active:
            header += " (active)"
        if not raw:
            header += " — effective view (default ⤥ named)"
        typer.echo(header, err=True)
        data = (
            target_profile.data
            if show_secrets
            else redact_secrets(
                target_profile.data, secret_field_paths(get_profile_settings_model())
            )
        )
        if fmt == "json":
            envelope = {
                "name": target_profile.name,
                "active": target_profile.is_active,
                "raw": raw,
                "data": data,
            }
            typer.echo(json.dumps(envelope))
        else:
            typer.echo(yaml.safe_dump(data, sort_keys=False, default_flow_style=False).rstrip())


@app.command("use", no_args_is_help=True)
def use_command(
    name: str = typer.Argument(..., help="Profile to activate."),
) -> None:
    """Persist ``active: <name>`` in the config file."""
    with report_errors():
        UseProfile(ProfileFileRepository())(name)
        typer.echo(f"active profile: {name} (config: {resolve_config_path()})", err=True)


@app.command("current")
def current_command(
    profile: ProfileOverrideOption = None,
) -> None:
    """Print the effective active profile name to stdout (pipe-friendly).

    Honours ``UNTAPED_PROFILE``, the root ``--profile`` flag, and this
    command's local ``--profile`` flag, falling back to ``default`` when
    none is set. The source of the answer (``env`` / ``config`` /
    ``fallback``) goes to stderr so stdout stays a single bare profile
    name suitable for piping.
    """
    with report_errors(), profile_override(profile):
        result = CurrentProfile(ProfileFileRepository())()
        typer.echo(result.name)
        typer.echo(f"(source: {result.source})", err=True)


@app.command("create", no_args_is_help=True)
def create_command(
    name: str = typer.Argument(..., help="Name of the new profile."),
    copy_from: str | None = typer.Option(
        None,
        "--copy-from",
        help="Existing profile to copy as a starting point.",
    ),
) -> None:
    """Create a new profile (empty by default; use ``--copy-from`` to seed it)."""
    with report_errors():
        CreateProfile(ProfileFileRepository())(name, copy_from=copy_from)
        suffix = f" (copied from {copy_from})" if copy_from else ""
        typer.echo(f"created profile: {name}{suffix}", err=True)


@app.command("delete", no_args_is_help=True)
def delete_command(
    name: str = typer.Argument(..., help="Profile to remove."),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Delete without interactive confirmation.",
    ),
) -> None:
    """Delete a profile. Refuses to delete the active profile."""
    with report_errors():
        repo = ProfileFileRepository()
        delete_profile = DeleteProfile(repo)
        preview = delete_profile.preview(name)
        if not yes:
            _confirm_delete(preview)
        delete_profile(name)
        typer.echo(f"deleted profile: {name}", err=True)


def _confirm_delete(preview: ProfileDeletePreview) -> None:
    if not _stdin_is_interactive():
        raise ConfigError("profile delete requires --yes when stdin is not interactive")

    top_level = ", ".join(preview.top_level_keys) or "(none)"
    typer.echo(f"config: {resolve_config_path()}", err=True)
    typer.echo(f"profile: {preview.name}", err=True)
    typer.echo(f"top-level keys: {top_level}", err=True)
    confirmed = typer.confirm(
        f"Delete profile {preview.name!r}?",
        default=False,
        err=True,
    )
    if not confirmed:
        typer.echo("delete cancelled", err=True)
        raise typer.Exit(code=1)


def _stdin_is_interactive() -> bool:
    return sys.stdin.isatty()


@app.command("rename", no_args_is_help=True)
def rename_command(
    old_name: str = typer.Argument(..., help="Existing profile name."),
    new_name: str = typer.Argument(..., help="New profile name."),
) -> None:
    """Rename a profile, updating ``active:`` if it pointed at the old name."""
    with report_errors():
        RenameProfile(ProfileFileRepository())(old_name, new_name)
        typer.echo(f"renamed profile: {old_name} → {new_name}", err=True)


def _profile_row(p: Profile) -> dict[str, object]:
    # ``name`` first: under ``--format raw`` the first key is what
    # pipelines feed back into the next command (xargs identifier
    # semantics). See root AGENTS.md '--format raw
    # default-column contract'; pinned by tests/unit/test_format_raw_first_key.py.
    return {
        "name": p.name,
        "active": "✓" if p.is_active else "",
        "keys": p.key_count,
    }
