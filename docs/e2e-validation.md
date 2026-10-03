# Desktop E2E validation

Validated on 3 October 2026: **25 passed, 0 failed, 0 skipped**, in 3.85 seconds. The [JUnit report](e2e-results.xml) records the run. This covers the opt-in `smart_display` entry point, not the legacy `Smart Display.py` script.

## Environment and reproduction

Linux, Python 3.14.7, Tk 8.6, pytest 9.1.1, requests 2.34.2 and Pillow 12.3.0. All Python dependencies were installed in the repository's `.venv`. The missing Tk/Xvfb/Openbox runtime was downloaded and extracted under `/tmp`; no system packages or global Python packages were installed.

With Python 3.11+ with Tkinter, Xvfb and Openbox available:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-test.txt
SMART_DISPLAY_SCREENSHOTS="$PWD/docs/screenshots" \
  .venv/bin/python tests/run_e2e.py -q --junitxml=docs/e2e-results.xml
```

The runner starts a fresh 1920×1080 virtual display, waits for its window manager, runs pytest and stops both processes. It never captures the user's desktop. Without `SMART_DISPLAY_SCREENSHOTS`, screenshots go into pytest's temporary directories. Running pytest directly without `DISPLAY` skips the six GUI tests, so use the runner to validate the whole suite.

On this machine the extracted runtime additionally required `PATH` and `LD_LIBRARY_PATH` to point to its `usr/bin` and `usr/lib`, `TCL_LIBRARY`/`TK_LIBRARY` to point to its Tcl/Tk directories, `XDG_DATA_DIRS` to include its `usr/share`, and `SMART_DISPLAY_OPENBOX_CONFIG` to select its bundled `rc.xml`. These settings applied only to the test command.

## Coverage

Each GUI scenario runs in a separate subprocess and enters the production CLI's real Tk mainloop. A test-only Tk factory captures the window and schedules assertions; navigation and exit use X11 XTEST mouse/keyboard events. Callback failures and hangs fail the test. Credentials and `.env` loading are isolated with fictional fixtures.

The provider scenario uses the production request parsing and refresh workers against a local HTTP server. Only the outbound request URL is redirected to localhost; request parameters, authorization header, timeouts and redirect policy are checked. The driver blocks external socket connections. Scheduled refresh deadlines are advanced to exercise outages without waiting a real minute.

| GUI scenario | Validated behavior | Local screenshot filenames |
| --- | --- | --- |
| Demo | Clock, Weather and Instagram navigation; invalid environment settings ignored; no HTTP requests; Close exits | `demo-clock.png`, `demo-weather.png`, `demo-instagram.png` |
| Resize | Content visible at 480×200 and 1280×720 | `demo-narrow.png`, `demo-large.png` |
| First run | Clock starts without credentials; missing integrations explain setup; return to clock; Escape exits | `first-run-clock.png`, `first-run-weather.png`, `first-run-instagram.png`, `first-run-narrow.png` |
| Provider lifecycle | Clock advances during a blocked weather request; loading status; correct next-day forecast; HTTP 503 retains value/timestamp as stale; Close exits with a pending request | `provider-refreshing.png`, `provider-weather.png`, `provider-stale.png` |
| Authentication | HTTP 400 Graph code 190 shows authentication required while preserving the follower reading; expired local token makes no HTTP request | `provider-authentication.png`, `expired-token.png` |
| Fullscreen / windowed | Fullscreen fills the 1920×1080 virtual display; Escape exits; `--windowed` overrides `FULLSCREEN=true` | `fullscreen-clock.png` |

There are six GUI scenarios; resize is part of demo and HTTP authentication is part of the provider scenario. The 19 focused tests cover configuration, import safety, single-flight refresh, retained data, late results, offline providers, and authentication/non-authentication error classification.

## Bug fixed during validation

The provider E2E initially failed: an HTTP 400 response containing Graph code 190 left the GUI at `stale`. The provider now classifies token/session codes 102 and 190 as `authentication required`, independently of the HTTP error status. Four focused authentication cases and three malformed/non-authentication response cases guard that behavior. The code-based classification is consistent with the [official archived Facebook SDK's error handling](https://github.com/facebookarchive/php-graph-sdk/blob/5.x/src/Facebook/Exceptions/FacebookResponseException.php); this is not a live API compatibility check.

## Screenshots

Fifteen unaltered captures of the application window with fictional data were visually inspected for readable content, status text and navigation. These generated PNGs remain local in `docs/screenshots/`, which is ignored by Git. They are not committed or embedded through repository URLs. Use the command above to regenerate them; the coverage table lists the output filenames.

## Limits

No Raspberry Pi/physical display or authenticated WeatherAPI/Meta request was tested. Provider fixtures are deterministic examples, not a complete current API contract review. The legacy settings, QR authentication, carousel, animations and original visual design still need migration; packaging and CI remain outstanding. PR #18 remains a draft.
