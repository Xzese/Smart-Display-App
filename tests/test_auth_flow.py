import os
from pathlib import Path
import runpy
import sys
import types
import unittest
from contextlib import contextmanager
from datetime import datetime, timedelta
from unittest.mock import patch

# The helper's public enum is the contract consumed by the application.
with patch.dict(os.environ, {}, clear=True):
    from auth_server import Outcome

from auth_flow import capture_outcome, outcome_message, outcome_succeeded


APP_PATH = Path(__file__).resolve().parents[1] / "Smart Display.py"


class FakeWidget:
    def __init__(self, *args, **values):
        self.args = args
        self.values = values
        self.values.setdefault("state", "normal")
        self.placed = False

    def configure(self, **values):
        self.values.update(values)

    config = configure

    def cget(self, name):
        return self.values.get(name, "")

    def place(self, **values):
        self.values.update(values)
        self.placed = True

    def place_configure(self, **values):
        self.values.update(values)
        self.placed = True

    def place_forget(self):
        self.placed = False

    def invoke(self):
        command = self.values.get("command")
        if command is not None:
            return command()


class FakeRoot(FakeWidget):
    def __init__(self):
        super().__init__()
        self.after_calls = []
        self.next_after_id = 1

    def after(self, delay, callback, *args):
        after_id = self.next_after_id
        self.next_after_id += 1
        self.after_calls.append((after_id, callback, args))
        return after_id

    def after_cancel(self, after_id):
        self.after_calls = [call for call in self.after_calls if call[0] != after_id]

    def run_next(self, callback):
        for index, (_, scheduled, args) in enumerate(self.after_calls):
            if scheduled is callback:
                del self.after_calls[index]
                return scheduled(*args)
        raise AssertionError("No scheduled callback matched {}".format(callback.__name__))

    def register(self, callback):
        return callback

    def geometry(self, value):
        self.values["geometry"] = value

    def title(self, value):
        self.values["title"] = value

    def attributes(self, *args):
        self.values["attributes"] = args

    def protocol(self, *args):
        self.values["protocol"] = args

    def destroy(self):
        self.values["destroyed"] = True

    def mainloop(self):
        pass


class FakeThread:
    def __init__(self, target):
        self.target = target
        self.running = False

    def start(self):
        self.running = True
        try:
            self.target()
        finally:
            self.running = False

    def is_alive(self):
        return self.running

    def join(self):
        pass


class FakeImage:
    size = (100, 100)

    def resize(self, size, resample=None):
        return self


class FakeResponse:
    status_code = 200
    text = ""

    def __init__(self, data):
        self.data = data

    def json(self):
        return self.data


@contextmanager
def load_headless_app(outcomes, auth_url_results=(), graph_version="v26.0"):
    root = FakeRoot()
    requests = types.ModuleType("requests")
    requests.get_calls = []

    def get(url, params=None, **kwargs):
        requests.get_calls.append((url, params, kwargs))
        if url.endswith("/me/accounts"):
            data = {"data": [{"instagram_business_account": {"id": "123456", "username": "display"}}]}
        else:
            data = {"followers_count": 42, "follows_count": 9, "media_count": 7}
        return FakeResponse(data)

    requests.get = get
    requests.post = lambda *args, **kwargs: None

    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda *args, **kwargs: None
    dotenv.set_key = lambda *args, **kwargs: None

    tkinter = types.ModuleType("tkinter")
    tkinter.Tk = lambda: root
    tkinter.Button = FakeWidget
    tkinter.Frame = FakeWidget
    tkinter.Label = FakeWidget
    tkinter.Entry = FakeWidget
    tkinter.StringVar = type("StringVar", (), {"set": lambda self, value: setattr(self, "value", value)})
    tkinter.NORMAL = "normal"
    tkinter.DISABLED = "disabled"

    qrcode = types.ModuleType("qrcode")

    class FakeQRCode:
        def __init__(self, **kwargs):
            pass

        def add_data(self, value):
            pass

        def make(self, fit=True):
            pass

        def make_image(self, **kwargs):
            return object()

    qrcode.QRCode = FakeQRCode
    qrcode.constants = types.SimpleNamespace(ERROR_CORRECT_L=1)

    pil = types.ModuleType("PIL")
    image = types.ModuleType("PIL.Image")
    image.open = lambda path: FakeImage()
    image.BICUBIC = 0
    image_tk = types.ModuleType("PIL.ImageTk")
    image_tk.PhotoImage = lambda source: object()
    pil.Image = image
    pil.ImageTk = image_tk

    threading = types.ModuleType("threading")
    threading.Thread = FakeThread

    class FakeSocket:
        def connect(self, address):
            pass

        def getsockname(self):
            return ("127.0.0.1", 0)

        def close(self):
            pass

    socket = types.ModuleType("socket")
    socket.socket = lambda *args, **kwargs: FakeSocket()
    socket.AF_INET = 2
    socket.SOCK_DGRAM = 2

    auth_server = types.ModuleType("auth_server")
    auth_server.Outcome = Outcome
    auth_server.get_graph_api_version = lambda: graph_version
    auth_server.stop_server = lambda: None
    auth_server.local_browser_capture = lambda: None
    auth_url_results = list(auth_url_results)
    auth_server.get_auth_url_calls = []

    def get_auth_url(*args, **kwargs):
        auth_server.get_auth_url_calls.append((args, kwargs))
        result = auth_url_results.pop(0) if auth_url_results else "https://facebook.example/oauth"
        if isinstance(result, Exception):
            raise result
        return result

    auth_server.get_auth_url = get_auth_url

    def wait_for_token():
        outcome = outcomes.pop(0)
        if outcome is Outcome.SUCCEEDED:
            os.environ["ACCESS_TOKEN"] = "fake-token"
            os.environ["ACCESS_TOKEN_EXPIRY"] = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S.%f")
        return outcome

    auth_server.wait_for_token = wait_for_token

    fake_modules = {
        "auth_server": auth_server,
        "dotenv": dotenv,
        "requests": requests,
        "tkinter": tkinter,
        "qrcode": qrcode,
        "PIL": pil,
        "PIL.Image": image,
        "PIL.ImageTk": image_tk,
        "threading": threading,
        "socket": socket,
    }
    initial_env = {
        "ACCESS_TOKEN_EXPIRY": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S.%f"),
        "CAROUSEL": "false",
        "PAGE_TRANSITION": "false",
        "PAGE_TRANSITION_TIME": "10",
        "FULLSCREEN": "false",
        "TEXT_FONT": "Arial",
        "DISPLAY_WIDTH": "1480",
        "DISPLAY_HEIGHT": "320",
        "IG_BUSINESS_USER_ID": "",
        "IG_LAST_UPDATED": "",
    }

    with patch.dict(os.environ, initial_env, clear=True), \
         patch.object(os, "chdir", lambda path: None), \
         patch.dict(sys.modules, fake_modules):
        namespace = runpy.run_path(str(APP_PATH), run_name="smart_display_headless_test")
        app = namespace["switch_to_settings"].__globals__
        yield app, root, requests, auth_server


class AuthFlowTests(unittest.TestCase):
    def test_only_real_helper_success_outcome_is_success(self):
        self.assertTrue(outcome_succeeded(Outcome.SUCCEEDED))
        for outcome in (
            Outcome.PENDING,
            Outcome.EXCHANGING,
            Outcome.DENIED,
            Outcome.CANCELLED,
            Outcome.TIMED_OUT,
            Outcome.FAILED,
        ):
            self.assertFalse(outcome_succeeded(outcome))
        self.assertIn("denied", outcome_message(Outcome.DENIED).lower())
        self.assertIn("timed out", outcome_message(Outcome.TIMED_OUT).lower())

    def test_worker_exception_becomes_real_helper_failure_outcome(self):
        def raise_error():
            raise RuntimeError("unexpected worker failure")

        self.assertIs(capture_outcome(raise_error, Outcome.FAILED), Outcome.FAILED)

    def test_settings_login_journey_retries_and_ignores_navigation_stale_result(self):
        outcomes = [Outcome.DENIED, Outcome.CANCELLED, Outcome.TIMED_OUT, Outcome.FAILED, Outcome.SUCCEEDED]
        with load_headless_app(
            outcomes,
            auth_url_results=[RuntimeError("APP_ID is required."), "https://facebook.example/oauth"],
        ) as (app, root, requests, auth_server):
            app["switch_to_settings"]()
            self.assertEqual(app["current_screen"], "Settings")

            # A missing Facebook setting is shown in the page instead of escaping the Tk callback.
            app["refresh_token_button"].invoke()
            self.assertEqual(app["current_screen"], "Settings")
            self.assertIn("APP_ID", app["auth_status_label"].cget("text"))
            self.assertEqual(app["refresh_token_button"].cget("text"), "Retry Login")

            expected_messages = (
                (Outcome.DENIED, "denied"),
                (Outcome.CANCELLED, "cancelled"),
                (Outcome.TIMED_OUT, "timed out"),
                (Outcome.FAILED, "login failed"),
            )
            for outcome, expected_message in expected_messages:
                app["refresh_token_button"].invoke()
                if outcome is Outcome.DENIED:
                    # A still-running listener must not be replaced by a retry.
                    app["auth_thread"].running = True
                    calls = len(auth_server.get_auth_url_calls)
                    app["refresh_token"]()
                    self.assertEqual(len(auth_server.get_auth_url_calls), calls)
                    self.assertIn("still stopping", app["auth_status_label"].cget("text"))
                    app["auth_thread"].running = False
                root.run_next(app["check_thread_status"])
                self.assertEqual(app["current_screen"], "Settings")
                self.assertEqual(app["instagram_button"].cget("state"), "disabled")
                self.assertIn(expected_message, app["auth_status_label"].cget("text").lower())
                self.assertEqual(app["refresh_token_button"].cget("text"), "Retry Login")

            # Retrying after failure succeeds and only then opens the clock/Instagram controls.
            app["refresh_token_button"].invoke()
            root.run_next(app["check_thread_status"])
            self.assertEqual(app["current_screen"], "Clock")
            self.assertEqual(app["instagram_button"].cget("state"), "normal")

            self.assertEqual(app["update_ig_stats"](), "IG Stats Updated Successfully")
            self.assertEqual(
                [call[0] for call in requests.get_calls],
                [
                    "https://graph.facebook.com/v26.0/me/accounts",
                    "https://graph.facebook.com/v26.0/123456",
                ],
            )
            self.assertTrue(all(args == () and kwargs == {} for args, kwargs in auth_server.get_auth_url_calls))

            # Delay one worker's completion across navigation and a newer attempt.
            outcomes[:] = [Outcome.DENIED, Outcome.SUCCEEDED]
            app["switch_to_settings"]()
            app["refresh_token_button"].invoke()
            app["switch_to_clock"]()
            app["switch_to_settings"]()
            app["refresh_token_button"].invoke()

            root.run_next(app["check_thread_status"])
            self.assertEqual(app["current_screen"], "Settings")
            self.assertFalse(app["auth_status_label"].placed)
            root.run_next(app["check_thread_status"])
            self.assertEqual(app["current_screen"], "Clock")


if __name__ == "__main__":
    unittest.main()
