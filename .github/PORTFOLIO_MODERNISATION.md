# Smart Display modernisation

Status: implementation started; keep the PR in draft.

## Implemented
- Opt-in `python -m smart_display` entry point with no import-time UI work.
- Credential-free demo through the same provider interface as live data.
- Optional window dimensions, display-derived defaults and fullscreen settings.
- Separate configuration, provider, refresh-state and UI modules.
- Background refresh, one in-flight call per provider and bounded network I/O waits.
- Last successful data, stale and authentication-required states.
- Original illustration/heading/readings/right-hand icon layout with responsive grid sizing, navigation and late-result-safe shutdown.
- Light/dark appearance with Settings choices Track system, Light and Dark; saved preferences and background desktop tracking.
- Twenty-nine focused tests and eight GUI E2E scenarios passed under Xvfb/Openbox.
- Reusable isolated desktop test runner, local HTTP provider fixtures and JUnit report; 23 screenshots captured and inspected locally, with generated screenshots ignored by Git.
- Graph error codes 102/190 now produce an authentication-required state even with HTTP 400.

## Remaining
- Migrate legacy integration settings, carousel, transitions and QR authentication.
- Integrate the explicit outcomes from the local OAuth PR before updating its submodule pin.
- Verify live Graph/Weather API contracts and the intended Raspberry Pi display.
- Add package metadata, CI and broader provider-contract fixtures.
- Retire the old script only after feature parity and a tested migration.

See docs/modernisation.md and docs/e2e-validation.md. The legacy script and auth pin are intentionally unchanged in this first pass.
