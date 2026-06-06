---
name: untaped-profile
description: Use the untaped profile plugin.
---

# Untaped Profile

Use this skill when the user wants an agent to operate `untaped profile` for configuration profile inventory.

## Setup

- The plugin command group is `untaped profile`.
- Profiles live in `~/.untaped/config.yml` unless `UNTAPED_CONFIG` is set.
- Read-time profile overrides use root `untaped --profile NAME ...` or command-local `--profile` on read commands.
- Mutating profile commands intentionally do not accept command-local `--profile`.

## Command Patterns

- `untaped profile list` lists known profiles and active state.
- `untaped profile current` prints the effective active profile name.
- `untaped profile show NAME` prints a profile with secrets redacted by default.
- `untaped profile create NAME`, `rename OLD NEW`, `use NAME`, and `delete NAME` mutate profile state.
- `delete` previews the target and requires interactive confirmation or `--yes`.

## Agent Guidance

- Prefer `--format json` when inspecting profile data programmatically.
- Do not reveal secrets unless the user explicitly requests a command option that does so.
- Compare against the persisted active profile for destructive operations; transient `UNTAPED_PROFILE` overrides must not rewrite active state.
