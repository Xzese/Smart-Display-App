from datetime import datetime, timezone
import threading
from unittest.mock import Mock

import pytest
from smart_display.core import DisplayConfig, RefreshTask, AuthenticationRequired
from smart_display.providers import configured_providers, instagram


def complete(task):
    task.thread.join(timeout=1)
    assert not task.thread.is_alive()
    return task.poll()


def test_first_run_without_credentials():
    config = DisplayConfig.from_env({})
    assert configured_providers(config) == {}
    assert config.fullscreen is False


@pytest.mark.parametrize("env", [{"DISPLAY_WIDTH": "0"}, {"DISPLAY_HEIGHT": "bad"}, {"DISPLAY_WIDTH": "9000"}, {"FULLSCREEN": "perhaps"}])
def test_invalid_settings_are_rejected(env):
    with pytest.raises(ValueError):
        DisplayConfig.from_env(env)


def test_demo_uses_no_network(monkeypatch):
    import requests
    monkeypatch.setattr(requests, "get", Mock(side_effect=AssertionError("Network is forbidden")))
    providers = configured_providers(DisplayConfig(), demo=True)
    assert "Sample data" in providers["Weather"]()
    assert "example_account" in providers["Instagram"]()
    requests.get.assert_not_called()


def test_last_good_value_is_retained_on_failure():
    fetch = Mock(side_effect=["16 °C", OSError("secret URL")])
    stamp = datetime(2026, 1, 1, tzinfo=timezone.utc)
    task = RefreshTask(fetch, now=lambda: stamp)
    task.start()
    assert complete(task).text == "16 °C"
    task.start()
    state = complete(task)
    assert state.text == "16 °C" and state.status == "stale" and state.updated_at == stamp
    assert "secret" not in repr(state)


def test_single_inflight_request_and_nonblocking_start():
    gate = threading.Event()
    task = RefreshTask(lambda: (gate.wait(timeout=1), "done")[1])
    assert task.start()
    assert not task.start()
    assert task.snapshot.status == "refreshing"
    gate.set()
    assert complete(task).status == "ready"


def test_close_ignores_late_worker_result():
    gate = threading.Event()
    task = RefreshTask(lambda: (gate.wait(timeout=1), "late")[1])
    task.start()
    task.close()
    before = task.snapshot
    gate.set()
    assert complete(task) == before
    assert not task.start()


def test_authentication_failure_is_distinct():
    task = RefreshTask(Mock(side_effect=AuthenticationRequired()))
    task.start()
    assert complete(task).status == "authentication required"


def test_missing_token_expiry_never_makes_a_request(monkeypatch):
    import requests
    monkeypatch.setattr(requests, "get", Mock())
    with pytest.raises(AuthenticationRequired):
        instagram(DisplayConfig(access_token="fixture", instagram_id="123"))
    requests.get.assert_not_called()


def test_importing_entrypoint_does_not_create_a_window(monkeypatch):
    import tkinter
    monkeypatch.setattr(tkinter, "Tk", Mock(side_effect=AssertionError("Unexpected window")))
    import smart_display.__main__
    tkinter.Tk.assert_not_called()
