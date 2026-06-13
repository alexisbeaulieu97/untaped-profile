"""Tests for the root --profile option handler."""

from __future__ import annotations

import os

import pytest
from untaped import get_settings

from untaped_profile.root_option import apply


@pytest.fixture(autouse=True)
def _clean_profile_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("UNTAPED_PROFILE", raising=False)


def test_apply_sets_env_and_invalidates_settings_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cleared: list[bool] = []
    monkeypatch.setattr(get_settings, "cache_clear", lambda: cleared.append(True))

    apply("stage")

    assert os.environ["UNTAPED_PROFILE"] == "stage"
    assert cleared == [True]
