"""Handler for the root ``--profile`` option this plugin contributes.

Core invokes :func:`apply` (lazily imported via ``RootOptionSpec`` in the
plugin manifest) before the dispatched command body reads settings, in any
token position.
"""

from __future__ import annotations

import os

from untaped.api import invalidate_settings_cache

from untaped_profile.domain.resolver import ACTIVE_PROFILE_ENV


def apply(profile: str) -> None:
    """Select ``profile`` for this invocation only."""
    os.environ[ACTIVE_PROFILE_ENV] = profile
    invalidate_settings_cache()
