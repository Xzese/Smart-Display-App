# Modern display entry point

This branch adds an opt-in application. It does not yet replace `Smart Display.py` or update the legacy authentication submodule.

## Try the offline demo

Use Python 3.11 or later with Tkinter installed. From the repository root, run:

```sh
python -m smart_display --demo
```

Demo mode ignores credentials and uses fictional provider data. It makes no provider requests. The clock still shows the local time. Escape or Close exits the application.

For live providers, install `requests` and `python-dotenv`. Copy `.env.example` to `.env`, set the required provider values, and run `python -m smart_display --windowed`.

Weather requires WEATHER_API_KEY and WEATHER_LOCATION. Instagram requires ACCESS_TOKEN, ACCESS_TOKEN_EXPIRY, IG_BUSINESS_USER_ID and an explicitly selected GRAPH_API_VERSION. The new application does not yet acquire or refresh tokens. Missing integrations leave the clock available.

## Design

`core.py` validates configuration and manages a single in-flight refresh per provider. Workers enqueue results; only the UI thread changes widgets. A failed refresh retains the last successful reading and marks it stale. Closing the application prevents late results from changing the display.

`providers.py` owns optional network requests. Connection/read timeouts bound stalled I/O, but are not a strict total wall-clock deadline for a trickling HTTP response. `__main__.py` owns startup, navigation, resize handling and shutdown. Importing these modules does not create a window or write configuration.

## Validation and remaining work

The suite now has 19 focused tests and six desktop E2E scenarios. All 25 passed locally under Xvfb/Openbox using a project virtual environment. The GUI tests exercise the production entry point, real X11 mouse/keyboard input, offline demo, first run, resize, fullscreen/windowed behavior, slow requests, stale data, authentication errors and shutdown. Fifteen screenshots were captured and inspected locally; generated screenshots are ignored by Git. The JUnit report is committed; see [E2E validation](e2e-validation.md) for reproduction commands and evidence.

Weather and Instagram responses in E2E tests come from a local HTTP fixture server; external network connections are blocked by the driver. No real device or authenticated WeatherAPI/Meta integration test was run.

The existing application's settings, QR authentication, carousel, animations and visual design have not yet been migrated. Keep the PR in draft until these gaps, packaging, CI and provider contracts are reviewed. The old script still has the limitations described in the audit.
