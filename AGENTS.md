# AGENTS.md — `untaped-profile`

Single source of truth for this standalone plugin repo. If you change
architecture, command behavior, settings behavior, or the development
workflow, update this file in the same commit.

## Mission

`untaped-profile` is an `untaped` plugin. It owns the **profile inventory**
in `~/.untaped/config.yml`: which profiles exist, which profile is active,
and how profiles are created, shown, selected, deleted, and renamed.
`untaped` core owns the binary, plugin discovery, config/profile resolution,
output helpers, and config-file primitives.

## Hard Rules

1. **Keep `AGENTS.md` up to date.** Architecture changes and new command
   patterns must be documented here.
2. **Prefer `uv` commands over manual dependency edits.** Use `uv add` and
   `uv add --group dev`; hand-edit tool config only.
3. **Expose the plugin through the `untaped.plugins` entry point.**
   `profile = "untaped_profile.plugin:plugin"` is the public integration
   point.
4. **Use the 4-layer DDD layout.** `cli -> application -> domain`, with
   `infrastructure -> domain`; `application` and `infrastructure` must not
   import each other at runtime.
5. **Declare ports in `application/ports.py`.** Use cases depend on the
   narrowest `Protocol`; concrete adapters satisfy ports structurally.
6. **Use absolute imports.** `from untaped_profile...` and `from untaped...`,
   never relative imports.
7. **Every source module has a module docstring.** Re-export `__init__.py`
   files are exempt.
8. **Every Typer app and every command with required args sets
   `no_args_is_help=True`.**
9. **stdout is data only.** Prompts, progress, and status messages go to
   stderr via `typer.echo(..., err=True)`.
10. **Pipe-friendly commands keep stable raw identifiers.** For `profile
    list`, `_profile_row()` must keep `name` as the first key.
11. **Secrets stay secret.** Redaction uses `secret_field_paths` from the
    installed `untaped` settings registry; never print known secret values
    unless the user passes `--show-secrets`.
12. **Finish with verification.** Run `uv run ruff check --fix`, `uv run ruff
    format`, `uv run mypy`, and `uv run pytest`.

## Architecture

```
src/untaped_profile/
├── __init__.py           # re-exports app
├── plugin.py             # entry-point plugin object
├── cli/                  # Typer commands; composition root
├── application/          # use cases and ports
├── domain/               # pure models
└── infrastructure/       # config-file adapter
```

Commands map one-to-one onto use cases in `application/`: `list`, `show`,
`use`, `current`, `create`, `delete`, and `rename`. Each use case talks to
`ProfileFileRepository` through the narrowest port in `application/ports.py`.
The adapter delegates every read and write to `untaped.config_file` and
`untaped.profile_resolver`; this package does not parse or write YAML itself.

## Active vs Persisted Active

`ProfileFileRepository` exposes two active-profile accessors:

- `active_name()` returns the effective active profile, honoring
  `UNTAPED_PROFILE`, the root `untaped --profile <name>` flag, and
  command-local read overrides such as
  `untaped profile show --profile <name>`.
- `persisted_active_name()` returns only the `active:` key on disk, ignoring
  per-call overrides.

The `list`, `show`, and `current` commands expose the core command-local
`ProfileOverrideOption` as `--profile` and wrap their reads in
`profile_override(profile)`. Mutating commands do not expose a command-local
profile selector. A transient profile override must never rewrite the user's
persisted active pointer. Mutating use cases that consult the active pointer
must compare against `persisted_active_name()`. `RenameProfile` delegates
active-pointer consistency to `untaped.config_file.rename_profile`, which
updates `active:` in the same locked mutation when the renamed profile was
persisted active.

## `current` Contract

`untaped profile current` returns `(name, source)`, where source is `env`,
`config`, or `fallback`. A command-local `--profile <name>` is implemented
through the same temporary env override as the root flag, so it reports
`env`. The name goes to stdout; `(source: ...)` goes to stderr.

When source is `env` or `config`, the use case validates that the named
profile exists. This protects the pipe pattern:

```bash
untaped --profile "$(untaped profile current)" ...
```

Fallback reports the conceptual `default` profile even if
`profiles.default` is absent, because schema defaults are then in effect.

## Mutation Invariants

- `CreateProfile` rejects empty names and collisions, and deep-copies
  `--copy-from` data.
- `DeleteProfile` refuses to delete the persisted active profile. The CLI
  previews the target and requires interactive confirmation or `--yes` before
  deleting. `default` is not special-cased when another profile is active.
- `RenameProfile` rejects empty new names, rejects renaming `default`, rejects
  `default` as a target, and preserves the persisted active pointer.

## Redaction

`profile show` redacts secrets in the CLI layer with:

```python
redact_secrets(profile.data, secret_field_paths(get_profile_settings_model()))
```

Both YAML and JSON output redact by default. `--show-secrets` is the only
path that reveals raw values. Redaction depends on settings sections
registered by installed plugins, so tests that assert AWX/GitHub token
redaction register small secret-bearing schemas explicitly.

## Development Workflow

```bash
uv sync
uv run pre-commit install
uv run pytest
uv run mypy
uv run ruff check --fix
uv run ruff format
uv run untaped profile --help
```

Use `pytest --no-cov` for tight local loops. Full `pytest` enforces the
coverage gate.

## Recipe: Add a Profile Sub-command

1. Write a use-case test with `FakeProfileRepository`.
2. Add or narrow a port in `application/ports.py` if the command needs new
   repository behavior.
3. Implement the use case in `application/`.
4. Wire the Typer command in `cli/commands.py`; keep stdout data-only.
5. If the command writes, add a `ProfileFileRepository` test against a temp
   `config.yml`.
6. Run `uv run untaped profile <command> --help` plus the full verification
   commands above.

## See Also

- [`untaped` core](https://github.com/alexisbeaulieu97/untaped) — plugin
  runtime, settings registry, config-file helpers, output helpers.
- [`untaped` configuration docs](https://github.com/alexisbeaulieu97/untaped/blob/main/docs/configuration.md)
  — user-facing profile and config behavior.
