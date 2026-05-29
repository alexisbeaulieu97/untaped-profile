# untaped-profile

`untaped-profile` is the profile-management plugin for
[`untaped`](https://github.com/alexisbeaulieu97/untaped). It adds the
`untaped profile` command group for listing, showing, creating, selecting,
deleting, and renaming profile blocks in `~/.untaped/config.yml`.

## Install

Install both `untaped` and this plugin from git:

```bash
uv tool install "git+https://github.com/alexisbeaulieu97/untaped.git" \
  --with "untaped-profile @ git+https://github.com/alexisbeaulieu97/untaped-profile.git" \
  --no-sources \
  --force
```

For managed plugin state, editable source installs, and multi-plugin sync
examples, see the core
[`untaped` plugin docs](https://github.com/alexisbeaulieu97/untaped/blob/main/docs/plugins.md).

## Commands

```text
untaped profile list
untaped profile current
untaped profile show <name>
untaped profile show <name> --raw
untaped profile show <name> --show-secrets
untaped profile use <name>
untaped profile create <name>
untaped profile create <name> --copy-from default
untaped profile delete <name>
untaped profile rename <old> <new>
```

`profile current` writes only the profile name to stdout so it can be used
in shell prompts and scripts. Source metadata goes to stderr.

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
