import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from smart_display.appearance import read_system_theme
from smart_display.core import DisplayConfig


@pytest.mark.parametrize("preference,expected", [(0, "dark"), (1, "dark"), (2, "light"), (99, "dark")])
def test_portal_appearance_values(monkeypatch, preference, expected):
    run = Mock(return_value=SimpleNamespace(returncode=0, stdout=f"(<<uint32 {preference}>>,)"))
    monkeypatch.setattr(subprocess, "run", run)
    assert read_system_theme() == expected
    assert run.call_args.kwargs["timeout"] == 1
    assert run.call_args.args[0][-2:] == ["org.freedesktop.appearance", "color-scheme"]


def test_older_portal_read_fallback(monkeypatch):
    run = Mock(side_effect=[SimpleNamespace(returncode=1, stdout=""), SimpleNamespace(returncode=0, stdout="(<<uint32 2>>,)" )])
    monkeypatch.setattr(subprocess, "run", run)
    assert read_system_theme() == "light"
    assert run.call_args_list[1].args[0][-3].endswith(".Read")


def test_gsettings_fallback(monkeypatch):
    run = Mock(side_effect=[SimpleNamespace(returncode=1, stdout=""), SimpleNamespace(returncode=1, stdout=""),
                            SimpleNamespace(returncode=0, stdout="'prefer-light'")])
    monkeypatch.setattr(subprocess, "run", run)
    assert read_system_theme() == "light"


@pytest.mark.parametrize("failure", [FileNotFoundError(), subprocess.TimeoutExpired("gdbus", 1)])
def test_unavailable_system_preference_preserves_dark_design(monkeypatch, failure):
    monkeypatch.setattr(subprocess, "run", Mock(side_effect=failure))
    assert read_system_theme() == "dark"


def test_window_size_is_optional():
    assert DisplayConfig().width is None and DisplayConfig().height is None
    assert DisplayConfig.from_env({"DISPLAY_WIDTH": "", "DISPLAY_HEIGHT": ""}).width is None


def test_invalid_theme_is_rejected():
    with pytest.raises(ValueError, match="DISPLAY_THEME"):
        DisplayConfig.from_env({"DISPLAY_THEME": "unknown"})
