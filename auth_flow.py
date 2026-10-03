"""Small, UI-independent helpers for the Smart Display login flow."""

from auth_server import Outcome


class AuthAttemptTracker:
    """Identify the one login attempt whose result may still update the UI."""

    def __init__(self):
        self._generation = 0
        self._active = None

    def begin(self, worker_alive=False):
        """Start a new attempt unless an earlier listener is still running."""
        if worker_alive:
            return None
        self._generation += 1
        self._active = self._generation
        return self._active

    def is_current(self, attempt):
        return attempt is not None and attempt == self._active

    def complete(self, attempt):
        """Consume the current attempt result; stale results are ignored."""
        if not self.is_current(attempt):
            return False
        self._active = None
        return True

    def cancel(self):
        """Invalidate pending callbacks for the current attempt."""
        self._generation += 1
        self._active = None


def capture_outcome(wait_for_token, failed_outcome):
    """Return the worker result, mapping unexpected exceptions to failure."""
    try:
        return wait_for_token()
    except Exception:
        return failed_outcome


def outcome_succeeded(outcome):
    """Only the explicit SUCCEEDED result authorizes leaving Settings."""
    return outcome is Outcome.SUCCEEDED


def outcome_message(outcome):
    """Give login results a short message suitable for the Settings screen."""
    name = getattr(outcome, "name", None) or str(outcome)
    messages = {
        "DENIED": "Facebook login was denied. You can try again.",
        "CANCELLED": "Login was cancelled. You can try again.",
        "TIMED_OUT": "Login timed out. You can try again.",
        "FAILED": "Login failed. Check your app settings and try again.",
    }
    return messages.get(name, "Login did not complete. You can try again.")


def graph_api_url(path, version):
    """Build a Graph API URL using the version configured by auth_server."""
    return "https://graph.facebook.com/{}/{}".format(version, path.lstrip("/"))
