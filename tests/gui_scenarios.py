"""Subprocess driver for the production CLI; provider HTTP is local fixture data."""
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import socket
import sys
import threading
import time
import tkinter as tk
import traceback
from urllib.parse import parse_qs, urlsplit

from PIL import ImageGrab
import requests
from Xlib import X, XK, display
from Xlib.ext import xtest

from smart_display import __main__ as entrypoint
from smart_display import ui


SCENARIO, TEMP = sys.argv[1], Path(sys.argv[2])
SCREENSHOTS = Path(os.environ.get("SMART_DISPLAY_SCREENSHOTS", str(TEMP / "screenshots")))
SCREENSHOTS.mkdir(parents=True, exist_ok=True)
errors = []
root = None
app = None
wire = display.Display()
gate = threading.Event()
calls = {"Weather": 0, "Instagram": 0}
network_attempts = []
server = None
system_preference = {"theme": "dark"}
ui.read_system_theme = lambda: system_preference["theme"]


class FixtureHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        parsed = urlsplit(self.path)
        if parsed.path == "/weather":
            calls["Weather"] += 1
            gate.wait(timeout=10)
            assert parse_qs(parsed.query)["q"] == ["Fixture Town"]
            if calls["Weather"] > 1:
                status, payload = 503, {"error": "fixture outage"}
            else:
                status, payload = 200, {
                    "location": {"localtime": "2026-10-03 17:00"},
                    "current": {"temp_c": 16, "condition": {"text": "Light cloud"}},
                    "forecast": {"forecastday": [
                        {"hour": [{"temp_c": 12, "condition": {"text": "Clear"}} for _ in range(24)]},
                        {"hour": [{"temp_c": 14, "condition": {"text": "Partly cloudy"}} for _ in range(24)]},
                    ]},
                }
        else:
            calls["Instagram"] += 1
            assert parsed.path == "/v99.0/123"
            assert parse_qs(parsed.query)["fields"] == ["username,followers_count"]
            assert self.headers["Authorization"] == "Bearer fictional-token"
            if calls["Instagram"] > 1:
                # Meta's structured invalid-token response can have HTTP 400.
                status, payload = 400, {"error": {"type": "OAuthException", "code": 190}}
            else:
                status, payload = 200, {"username": "fixture_account", "followers_count": 1234}
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass


original_request = requests.sessions.Session.request
original_connect = socket.socket.connect


def local_connect(sock, address):
    if sock.family in (socket.AF_INET, socket.AF_INET6):
        network_attempts.append(address)
        assert server is not None and address[0] == "127.0.0.1", "External network forbidden"
    return original_connect(sock, address)


socket.socket.connect = local_connect


def local_request(session, method, url, **kwargs):
    assert server is not None, "Demo/first-run/expired must make no HTTP requests"
    assert kwargs["timeout"] == (5, 15)
    assert kwargs["allow_redirects"] is False
    parsed = urlsplit(url)
    assert parsed.netloc in {"api.weatherapi.com", "graph.facebook.com"}
    path = "/weather" if parsed.netloc == "api.weatherapi.com" else parsed.path
    session.trust_env = False
    return original_request(session, method, f"http://127.0.0.1:{server.server_port}{path}", **kwargs)


requests.sessions.Session.request = local_request


def widgets(parent):
    for child in parent.winfo_children():
        yield child
        yield from widgets(child)


def click(name):
    button = next(w for w in widgets(root) if isinstance(w, (tk.Button, tk.Radiobutton)) and w.cget("text") == name and w.winfo_ismapped())
    xtest.fake_input(wire, X.MotionNotify, x=button.winfo_rootx() + button.winfo_width() // 2,
                     y=button.winfo_rooty() + button.winfo_height() // 2)
    xtest.fake_input(wire, X.ButtonPress, 1)
    xtest.fake_input(wire, X.ButtonRelease, 1)
    wire.sync()


def escape():
    root.focus_force()
    keycode = wire.keysym_to_keycode(XK.string_to_keysym("Escape"))
    xtest.fake_input(wire, X.KeyPress, keycode)
    xtest.fake_input(wire, X.KeyRelease, keycode)
    wire.sync()


def value():
    return app.content_text()


def close_app():
    click("Settings")
    yield from wait(lambda: app.screen == "Settings" and app.close_button.winfo_ismapped(), "settings close control")
    click("Close App")


def assert_readable():
    from tkinter import font
    for widget in app.labels.values():
        if widget.winfo_ismapped() and widget.cget("text"):
            actual_font = font.Font(root, font=widget.cget("font"))
            assert max(actual_font.measure(line) for line in widget.cget("text").splitlines()) <= widget.winfo_width(), widget.cget("text")
            assert widget.winfo_reqheight() <= widget.winfo_height(), widget.cget("text")
    for widget in app.theme_choices.values():
        if widget.winfo_ismapped():
            assert widget.winfo_reqwidth() <= widget.winfo_width(), widget.cget("text")
            assert widget.winfo_reqheight() <= widget.winfo_height(), widget.cget("text")


def status():
    return app.status.cget("text")


def wait(predicate, description, timeout=4):
    end = time.monotonic() + timeout
    while not predicate():
        assert time.monotonic() < end, f"Timed out: {description}; value={value()!r}, status={status()!r}"
        yield


def capture(name):
    root.update_idletasks()
    if not name.startswith("failure-"):
        assert_readable()
    x, y = root.winfo_rootx(), root.winfo_rooty()
    size = root.winfo_width(), root.winfo_height()
    shot = ImageGrab.grab(bbox=(x, y, x + size[0], y + size[1]), xdisplay=os.environ["DISPLAY"])
    assert shot.size == size and len(shot.getcolors(shot.width * shot.height)) > 2
    shot.save(SCREENSHOTS / f"{name}.png")


def flow():
    yield from wait(lambda: root.winfo_viewable(), "window mapped")
    yield from wait(lambda: app.value.winfo_ismapped(), "clock content mapped")
    yield from wait(lambda: status() == "Local time", "clock startup")
    assert ":" in value() and "\n" in value()
    if SCENARIO != "saved-theme":
        assert root.cget("bg") == "#000000" and app.value.cget("fg") == "#ffffff"
    assert app.labels["title"].cget("text") == "Time"
    assert app.logo.cget("image")
    assert app.navigation["Clock"].winfo_rootx() > app.value.winfo_rootx()
    assert all(button.cget("image") for button in app.navigation.values())
    if SCENARIO == "demo":
        assert root.title() == "Smart Display · Demo"
        assert (root.winfo_width(), root.winfo_height()) == (round(root.winfo_screenwidth() * 0.75), round(root.winfo_screenheight() * 0.75))
        capture("demo-clock")
        click("Weather")
        yield from wait(lambda: "Sample data" in value() and status().startswith("ready"), "demo weather")
        assert "16 °C" in value()
        capture("demo-weather")
        click("Instagram")
        yield from wait(lambda: app.value.cget("text") == "1,234" and "example_account" in value(), "demo Instagram")
        assert app.labels["title"].cget("text") == "Followers"
        assert "example_account" in value()
        capture("demo-instagram")
        root.geometry("1480x320")
        yield from wait(lambda: root.winfo_width() == 1480, "wide display resize")
        assert_readable()
        capture("demo-wide")
        root.geometry("480x200")
        yield from wait(lambda: root.winfo_width() == 480, "narrow resize")
        assert_readable()
        capture("demo-narrow")
        root.geometry("1280x720")
        yield from wait(lambda: root.winfo_width() == 1280, "large resize")
        capture("demo-large")
        assert not network_attempts
        click("Settings")
        yield from wait(lambda: app.theme_choices["light"].winfo_ismapped(), "demo appearance choices")
        click("Light")
        yield from wait(lambda: app.theme == "light", "demo light theme")
        assert not (TEMP / ".env").exists(), "Demo appearance must not change live settings"
        for name in ("Weather", "Instagram"):
            click(name)
            yield from wait(lambda: app.screen == name and "Sample data" in value(), f"light {name}")
            assert root.cget("bg") == "#ffffff"
            capture(f"light-{name.lower()}")
        yield from close_app()
    elif SCENARIO == "first-run":
        assert root.title() == "Smart Display" and not app.tasks
        capture("first-run-clock")
        for name in ("Weather", "Instagram"):
            click(name)
            yield from wait(lambda: f"{name} is not configured" in value(), f"missing {name}")
            assert "clock remains available" in status()
            capture(f"first-run-{name.lower()}")
        root.geometry("480x200")
        yield from wait(lambda: root.winfo_width() == 480, "first-run narrow resize")
        capture("first-run-narrow")
        assert app.status.winfo_reqwidth() <= root.winfo_width(), "Setup status is clipped on narrow displays"
        click("Clock")
        yield from wait(lambda: status() == "Local time", "return to clock")
        assert not network_attempts
        escape()
    elif SCENARIO == "providers":
        yield from wait(lambda: calls["Weather"] == 1, "slow weather request started")
        clock = value()
        yield from wait(lambda: value() != clock, "clock advances while weather blocks", timeout=2)
        click("Weather")
        yield from wait(lambda: status() == "refreshing", "loading weather")
        capture("provider-refreshing")
        assert calls["Weather"] == 1
        gate.set()
        yield from wait(lambda: status().startswith("ready") and app.labels["future_temp"].cget("text") == "14 °C" and "Partly cloudy" in value(), "weather HTTP fixture")
        assert app.labels["future_label"].cget("text") == "Tomorrow"
        assert app.labels["future_conditions"].cget("text") == "Partly cloudy"
        last_value, stamp = value(), app.tasks["Weather"].snapshot.updated_at
        capture("provider-weather")
        # Advance the scheduled refresh without waiting a real minute.
        app.next_refresh["Weather"] = 0
        yield from wait(lambda: status().startswith("stale"), "HTTP outage becomes stale")
        assert value() == last_value and app.tasks["Weather"].snapshot.updated_at == stamp
        capture("provider-stale")
        click("Instagram")
        yield from wait(lambda: "fixture_account" in value() and status().startswith("ready"), "Instagram HTTP fixture")
        assert app.value.cget("text") == "1,234"
        last_value = value()
        app.next_refresh["Instagram"] = 0
        yield from wait(lambda: status().startswith("authentication required"), "HTTP 400 invalid token becomes auth required")
        assert value() == last_value
        capture("provider-authentication")
        # Shutdown while a real HTTP worker is still waiting.
        gate.clear()
        app.next_refresh["Weather"] = 0
        yield from wait(lambda: calls["Weather"] == 3, "pending worker before close")
        yield from close_app()
    elif SCENARIO == "expired":
        click("Instagram")
        yield from wait(lambda: status() == "authentication required", "expired token")
        assert not network_attempts
        capture("expired-token")
        escape()
    elif SCENARIO == "windowed":
        assert not root.attributes("-fullscreen")
        assert (root.winfo_width(), root.winfo_height()) == (round(root.winfo_screenwidth() * 0.75), round(root.winfo_screenheight() * 0.75))
        assert not network_attempts
        escape()
    elif SCENARIO == "appearance":
        from dotenv import dotenv_values
        click("Settings")
        yield from wait(lambda: app.theme_choices["light"].winfo_ismapped(), "appearance choices")
        assert app.theme_mode.get() == "system"
        capture("settings-dark")
        root.geometry("480x200")
        yield from wait(lambda: root.winfo_width() == 480 and root.winfo_height() == 200, "compact settings")
        yield
        capture("settings-narrow")
        root.geometry(f"{round(root.winfo_screenwidth() * 0.75)}x{round(root.winfo_screenheight() * 0.75)}")
        yield from wait(lambda: root.winfo_width() > 480, "restore settings window")
        yield
        click("Light")
        yield from wait(lambda: app.theme == "light" and root.cget("bg") == "#e6e6e6", "light settings")
        assert dotenv_values(TEMP / ".env")["DISPLAY_THEME"] == "light"
        capture("settings-light")
        click("Clock")
        yield from wait(lambda: app.screen == "Clock" and root.cget("bg") == "#ffffff", "light clock")
        assert app.value.cget("fg") == "#000000"
        capture("light-clock")
        click("Settings")
        yield from wait(lambda: app.theme_choices["dark"].winfo_ismapped(), "dark appearance control")
        system_preference["theme"] = "light"
        click("Dark")
        yield from wait(lambda: app.theme == "dark", "explicit dark ignores light system preference")
        assert dotenv_values(TEMP / ".env")["DISPLAY_THEME"] == "dark"
        click("Track system")
        yield from wait(lambda: app.theme == "light", "track system light")
        assert dotenv_values(TEMP / ".env")["DISPLAY_THEME"] == "system"
        capture("settings-track-system")
        system_preference["theme"] = "dark"
        yield from wait(lambda: app.theme == "dark", "track system updates while running")
        click("Clock")
        yield from wait(lambda: root.cget("bg") == "#000000", "return to original dark clock")
        assert not network_attempts
        escape()
    elif SCENARIO == "saved-theme":
        assert app.theme_mode.get() == "light" and app.theme == "light"
        assert root.cget("bg") == "#ffffff"
        escape()
    else:
        yield from wait(lambda: bool(root.attributes("-fullscreen")) and
                        root.winfo_width() == wire.screen().width_in_pixels, "fullscreen startup")
        capture("fullscreen-clock")
        escape()
    yield


real_tk, real_app = tk.Tk, entrypoint.DisplayApp


def record_error(kind, error, tb):
    errors.append("".join(traceback.format_exception(kind, error, tb)))
    if app is not None:
        try:
            capture(f"failure-{SCENARIO}")
        except Exception:
            pass
        app.close()
    else:
        root.destroy()


def create_root():
    global root
    root = real_tk()
    root.report_callback_exception = record_error
    steps = flow()

    def step():
        try:
            next(steps)
        except StopIteration:
            record_error(AssertionError, AssertionError("GUI did not close"), None)
            return
        except BaseException:
            record_error(*sys.exc_info())
            return
        if not app.closed:
            root.after(25, step)

    root.after(100, step)
    root.after(15000, lambda: record_error(AssertionError, AssertionError("GUI watchdog expired"), None))
    return root


def create_app(*args, **kwargs):
    global app
    app = real_app(*args, **kwargs)
    return app


tk.Tk = create_root
entrypoint.DisplayApp = create_app

args = []
if SCENARIO == "demo":
    args = ["--demo"]
    # Demo must ignore even invalid credentials and dimensions.
    os.environ.update(DISPLAY_WIDTH="invalid", ACCESS_TOKEN="fictional-token")
elif SCENARIO in {"providers", "expired"}:
    expiry = datetime.now(timezone.utc) + timedelta(days=1 if SCENARIO == "providers" else -1)
    (TEMP / ".env").write_text(
        f"ACCESS_TOKEN=fictional-token\nIG_BUSINESS_USER_ID=123\nGRAPH_API_VERSION=v99.0\n"
        f"ACCESS_TOKEN_EXPIRY={expiry.isoformat()}\n"
        + ("WEATHER_API_KEY=fictional-key\nWEATHER_LOCATION=Fixture Town\n" if SCENARIO == "providers" else "")
    )
    if SCENARIO == "providers":
        server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
elif SCENARIO in {"fullscreen", "windowed"}:
    os.environ["FULLSCREEN"] = "true"
    if SCENARIO == "windowed":
        args = ["--windowed"]
elif SCENARIO == "saved-theme":
    (TEMP / ".env").write_text("DISPLAY_THEME=light\n")

try:
    assert entrypoint.main(args, env_path=TEMP / ".env") == 0
    assert app.closed and all(task.closed for task in app.tasks.values())
    assert not errors, "\n".join(errors)
    print(f"PASS {SCENARIO}; HTTP requests: {calls}")
finally:
    gate.set()
    if app is not None:
        for task in app.tasks.values():
            if task.thread is not None:
                task.thread.join(timeout=2)
        assert all(not task.thread or not task.thread.is_alive() for task in app.tasks.values())
    if server is not None:
        server.shutdown()
        server.server_close()
    wire.close()
