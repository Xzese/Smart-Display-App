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
                        {"hour": [{"temp_c": 12} for _ in range(24)]},
                        {"hour": [{"temp_c": 14} for _ in range(24)]},
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
    button = next(w for w in widgets(root) if isinstance(w, tk.Button) and w.cget("text") == name)
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
    return app.value.cget("text")


def status():
    return app.status.cget("text")


def wait(predicate, description, timeout=4):
    end = time.monotonic() + timeout
    while not predicate():
        assert time.monotonic() < end, f"Timed out: {description}; value={value()!r}, status={status()!r}"
        yield


def capture(name):
    root.update_idletasks()
    x, y = root.winfo_rootx(), root.winfo_rooty()
    size = root.winfo_width(), root.winfo_height()
    shot = ImageGrab.grab(bbox=(x, y, x + size[0], y + size[1]), xdisplay=os.environ["DISPLAY"])
    assert shot.size == size and len(shot.getcolors(shot.width * shot.height)) > 2
    shot.save(SCREENSHOTS / f"{name}.png")


def flow():
    yield from wait(lambda: root.winfo_viewable(), "window mapped")
    assert app.value.winfo_ismapped()
    yield from wait(lambda: status() == "Local time", "clock startup")
    assert ":" in value() and "\n" in value()
    if SCENARIO == "demo":
        assert root.title() == "Smart Display · Demo"
        assert (root.winfo_width(), root.winfo_height()) == (960, 320)
        capture("demo-clock")
        click("Weather")
        yield from wait(lambda: "Sample data" in value() and status().startswith("ready"), "demo weather")
        assert "16 °C" in value()
        capture("demo-weather")
        click("Instagram")
        yield from wait(lambda: "1,234 followers" in value(), "demo Instagram")
        assert "example_account" in value()
        capture("demo-instagram")
        root.geometry("480x200")
        yield from wait(lambda: root.winfo_width() == 480, "narrow resize")
        assert app.value.winfo_reqwidth() <= 480
        assert app.value.winfo_reqheight() <= app.value.winfo_height()
        capture("demo-narrow")
        root.geometry("1280x720")
        yield from wait(lambda: root.winfo_width() == 1280, "large resize")
        capture("demo-large")
        assert not network_attempts
        click("Close")
    elif SCENARIO == "first-run":
        assert root.title() == "Smart Display" and not app.tasks
        capture("first-run-clock")
        for name in ("Weather", "Instagram"):
            click(name)
            yield from wait(lambda: value() == f"{name} is not configured", f"missing {name}")
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
        yield from wait(lambda: status().startswith("ready") and "Tomorrow: 14 °C" in value(), "weather HTTP fixture")
        last_value, stamp = value(), app.tasks["Weather"].snapshot.updated_at
        capture("provider-weather")
        # Advance the scheduled refresh without waiting a real minute.
        app.next_refresh["Weather"] = 0
        yield from wait(lambda: status().startswith("stale"), "HTTP outage becomes stale")
        assert value() == last_value and app.tasks["Weather"].snapshot.updated_at == stamp
        capture("provider-stale")
        click("Instagram")
        yield from wait(lambda: "fixture_account" in value() and status().startswith("ready"), "Instagram HTTP fixture")
        assert "1,234 followers" in value()
        last_value = value()
        app.next_refresh["Instagram"] = 0
        yield from wait(lambda: status().startswith("authentication required"), "HTTP 400 invalid token becomes auth required")
        assert value() == last_value
        capture("provider-authentication")
        # Shutdown while a real HTTP worker is still waiting.
        gate.clear()
        app.next_refresh["Weather"] = 0
        yield from wait(lambda: calls["Weather"] == 3, "pending worker before close")
        click("Close")
    elif SCENARIO == "expired":
        click("Instagram")
        yield from wait(lambda: status() == "authentication required", "expired token")
        assert not network_attempts
        capture("expired-token")
        escape()
    elif SCENARIO == "windowed":
        assert not root.attributes("-fullscreen")
        assert (root.winfo_width(), root.winfo_height()) == (960, 320)
        assert not network_attempts
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

# Read an isolated .env fixture, not the checkout's personal .env.
import dotenv
real_load = dotenv.load_dotenv
dotenv.load_dotenv = lambda *args, **kwargs: real_load(TEMP / ".env")

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

try:
    assert entrypoint.main(args) == 0
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
