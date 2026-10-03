"""Real Tk mainloop, X11 mouse/keyboard input and captured pixels.

Run on a dedicated Xvfb display, never on a personal desktop:
    .venv/bin/python tests/run_e2e.py -q
"""
import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize("scenario", ["demo", "first-run", "providers", "expired", "fullscreen", "windowed", "appearance", "saved-theme"])
def test_desktop_entrypoint(scenario, tmp_path):
    if not os.environ.get("DISPLAY"):
        pytest.skip("GUI E2E requires an X11 display; use xvfb-run")
    env = os.environ.copy()
    for key in (
        "DISPLAY_WIDTH", "DISPLAY_HEIGHT", "FULLSCREEN", "WEATHER_API_KEY",
        "WEATHER_LOCATION", "GRAPH_API_VERSION", "IG_BUSINESS_USER_ID",
        "ACCESS_TOKEN", "ACCESS_TOKEN_EXPIRY",
        "DISPLAY_THEME", "TEXT_FONT",
    ):
        env.pop(key, None)
    project = Path(__file__).resolve().parents[1]
    env["PYTHONPATH"] = str(project)
    result = subprocess.run(
        [sys.executable, str(project / "tests" / "gui_scenarios.py"), scenario, str(tmp_path)],
        env=env, cwd=tmp_path, capture_output=True, text=True, timeout=25,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"PASS {scenario}" in result.stdout
