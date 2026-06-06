# untaped-profile

`untaped-profile` is the profile-management plugin for
[`untaped`](https://github.com/alexisbeaulieu97/untaped). It adds the
`untaped profile` command group for listing, showing, creating, selecting,
deleting, and renaming profile blocks in `~/.untaped/config.yml`.

## Install

Install both `untaped` and this plugin from git:

```bash
uv tool install "git+https://github.com/alexisbeaulieu97/untaped.git@v0.1.1" \
  --with "untaped-profile @ git+https://github.com/alexisbeaulieu97/untaped-profile.git@v0.1.0" \
  --no-sources \
  --force
```

For managed plugin state, editable source installs, and multi-plugin sync
examples, see the core
[`untaped` plugin docs](https://github.com/alexisbeaulieu97/untaped/blob/main/docs/plugins.md).

This plugin also contributes the `untaped-profile` agent skill. After the
plugin is installed, use the core
[`untaped` agent skill docs](https://github.com/alexisbeaulieu97/untaped/blob/main/docs/skills.md)
to install it for Codex or Claude.

## Commands

```text
untaped profile list
untaped profile list --profile work
untaped profile current
untaped profile current --profile work
untaped profile show
untaped profile show --profile work
untaped profile show <name>
untaped profile show <name> --raw
untaped profile show <name> --show-secrets
untaped profile use <name>
untaped profile create <name>
untaped profile create <name> --copy-from default
untaped profile delete <name>
untaped profile delete <name> --yes
untaped profile rename <old> <new>
```

`profile list`, `profile current`, and `profile show` accept command-local
`--profile <name>` when you want to inspect a profile other than the
persisted active profile. Mutation commands keep their explicit name
arguments and do not use command-local profile selection.

`profile current` writes only the profile name to stdout so it can be used
in shell prompts and scripts. Source metadata goes to stderr.

`profile show` without a name inspects the current effective profile. Pass a
name only when inspecting a different profile.

`profile delete` asks for confirmation in an interactive terminal and refuses
non-interactive deletes unless `--yes` is passed.

## Development

```bash
uv sync
uv run pytest
uv run mypy
uv run ruff check --fix
uv run ruff format
uv run untaped profile --help
```

See [AGENTS.md](./AGENTS.md) for architecture rules and profile-specific
invariants.
