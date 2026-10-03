"""Validated configuration and a UI-independent refresh lifecycle."""
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from queue import Empty, Queue
import threading


@dataclass(frozen=True)
class DisplayConfig:
    width: int | None = None
    height: int | None = None
    fullscreen: bool = False
    text_font: str = "Arial Rounded MT Bold"
    theme: str = "system"
    weather_key: str = field(default="", repr=False)
    weather_location: str = ""
    graph_version: str = ""
    instagram_id: str = ""
    access_token: str = field(default="", repr=False)
    token_expiry: str = ""

    @classmethod
    def from_env(cls, env):
        def dimension(name):
            raw = env.get(name, "")
            if not raw:
                return None
            if not raw.isascii() or not raw.isdigit() or not 200 <= int(raw) <= 8192:
                raise ValueError(f"{name} must be between 200 and 8192 pixels.")
            return int(raw)
        fullscreen = env.get("FULLSCREEN", "false").lower()
        if fullscreen not in {"true", "false"}:
            raise ValueError("FULLSCREEN must be true or false.")
        theme = env.get("DISPLAY_THEME", "system").lower()
        if theme not in {"system", "light", "dark"}:
            raise ValueError("DISPLAY_THEME must be system, light or dark.")
        return cls(
            width=dimension("DISPLAY_WIDTH"), height=dimension("DISPLAY_HEIGHT"),
            fullscreen=fullscreen == "true", weather_key=env.get("WEATHER_API_KEY", ""),
            text_font=env.get("TEXT_FONT", "Arial Rounded MT Bold"), theme=theme,
            weather_location=env.get("WEATHER_LOCATION", ""), graph_version=env.get("GRAPH_API_VERSION", ""),
            instagram_id=env.get("IG_BUSINESS_USER_ID", ""), access_token=env.get("ACCESS_TOKEN", ""),
            token_expiry=env.get("ACCESS_TOKEN_EXPIRY", ""),
        )


class AuthenticationRequired(RuntimeError):
    pass


@dataclass(frozen=True)
class Snapshot:
    text: str = "No data yet"
    status: str = "not configured"
    updated_at: datetime | None = None


class RefreshTask:
    """Workers only enqueue results. The UI thread calls poll() to apply them."""
    def __init__(self, fetch, *, now=lambda: datetime.now(timezone.utc)):
        self.fetch = fetch
        self.now = now
        self.snapshot = Snapshot(status="waiting")
        self.results = Queue(maxsize=1)
        self.busy = False
        self.closed = False
        self.thread = None

    def start(self):
        if self.closed or self.busy:
            return False
        self.busy = True
        self.snapshot = replace(self.snapshot, status="refreshing")
        def worker():
            try:
                text = self.fetch()
                if not isinstance(text, str):
                    raise ValueError("Provider did not return text.")
                result = ("ready", text)
            except AuthenticationRequired:
                result = ("authentication required", None)
            except Exception:
                # Do not expose provider URLs or credentials through error text.
                result = ("unavailable", None)
            self.results.put(result)
        self.thread = threading.Thread(target=worker, daemon=True)
        self.thread.start()
        return True

    def poll(self):
        try:
            status, text = self.results.get_nowait()
        except Empty:
            return self.snapshot
        self.busy = False
        if self.closed:
            return self.snapshot
        if status == "ready":
            self.snapshot = Snapshot(text, status, self.now())
        else:
            label = "stale" if status == "unavailable" and self.snapshot.updated_at else status
            self.snapshot = replace(self.snapshot, status=label)
        return self.snapshot

    def close(self):
        self.closed = True
