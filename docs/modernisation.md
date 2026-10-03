# Modern display entry point

This branch adds an opt-in application. It does not yet replace `Smart Display.py` or update the legacy authentication submodule.

## Try the offline demo

Use Python 3.11 or later with Tkinter installed. From the repository root, install the application dependencies in a virtual environment:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-modern.txt
.venv/bin/python -m smart_display --demo
```

Demo mode ignores credentials and uses fictional provider data. It makes no provider requests. The clock still shows the local time. Escape or Close exits the application.

For live providers, copy `.env.example` to `.env`, set the required provider values, and run `.venv/bin/python -m smart_display --windowed`.

Weather requires WEATHER_API_KEY and WEATHER_LOCATION. Instagram requires ACCESS_TOKEN, ACCESS_TOKEN_EXPIRY, IG_BUSINESS_USER_ID and an explicitly selected GRAPH_API_VERSION. The new application does not yet acquire or refresh tokens. Missing integrations leave the clock available.

## Appearance and layout

The original layout places an illustration on the left, a heading and large readings in the centre, and icon navigation on the right. Tk grid sizing and text fitting use the actual viewport, with no fixed design resolution. A window initially uses 75% of the current display; fullscreen fills it. `DISPLAY_WIDTH` and `DISPLAY_HEIGHT` are optional explicit overrides. The original `TEXT_FONT` is used when installed, otherwise Arial.

Settings offers **Track system**, **Light** and **Dark**. Selection updates immediately and is saved as `DISPLAY_THEME=system|light|dark` in the project `.env`; demo selections apply only to that session. Track system polls the Linux desktop appearance portal in a background worker every two seconds, with a GNOME settings fallback. If the desktop has no preference, the original dark appearance is retained. Portal values follow the [desktop Settings specification](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.Settings.html).

## Design

`core.py` validates configuration and manages a single in-flight refresh per provider. Workers enqueue results; only the UI thread changes widgets. A failed refresh retains the last successful reading and marks it stale. Closing the application prevents late results from changing the display.

`providers.py` owns optional network requests. Connection/read timeouts bound stalled I/O, but are not a strict total wall-clock deadline for a trickling HTTP response. `__main__.py` owns startup and preference persistence; `ui.py` owns navigation, layout and shutdown. `appearance.py` reads the desktop preference without changing host settings. Importing these modules does not create a window or write configuration.

## Validation and remaining work

The suite now has 29 focused tests and eight desktop E2E scenarios. All 37 passed locally under Xvfb/Openbox using a project virtual environment. The GUI tests exercise the production entry point, real X11 mouse/keyboard input, offline demo, first run, resize, fullscreen/windowed behavior, slow requests, stale data, authentication errors, theme switching, preference persistence, dynamic system tracking and shutdown. Twenty-three screenshots were captured and inspected locally; generated screenshots are ignored by Git. The JUnit report is committed; see [E2E validation](e2e-validation.md) for reproduction commands and evidence.

Weather and Instagram responses in E2E tests come from a local HTTP fixture server; external network connections are blocked by the driver. No real device or authenticated WeatherAPI/Meta integration test was run.

The original screen arrangement has been restored; legacy integration settings, QR authentication, carousel and animations still need migration. Keep the PR in draft until these gaps, packaging, CI and provider contracts are reviewed. The old script still has the limitations described in the audit.
