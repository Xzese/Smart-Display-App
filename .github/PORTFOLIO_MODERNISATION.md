# Smart Display modernisation

Status: implementation started; keep the PR in draft.

## Implemented
- Opt-in `python -m smart_display` entry point with no import-time UI work.
- Credential-free demo through the same provider interface as live data.
- Validated dimensions and fullscreen settings.
- Separate configuration, provider, refresh-state and UI modules.
- Background refresh, one in-flight call per provider and bounded network I/O waits.
- Last successful data, stale and authentication-required states.
- Basic resizing, navigation and late-result-safe shutdown.
- Nineteen focused tests and six GUI E2E scenarios passed under Xvfb/Openbox.
- Reusable isolated desktop test runner, local HTTP provider fixtures and JUnit report; 15 screenshots captured and inspected locally, with generated screenshots ignored by Git.
- Graph error codes 102/190 now produce an authentication-required state even with HTTP 400.

## Remaining
- Migrate settings, carousel, transitions, original visual design and QR authentication.
- Integrate the explicit outcomes from the local OAuth PR before updating its submodule pin.
- Verify live Graph/Weather API contracts and the intended Raspberry Pi display.
- Add package metadata, CI and broader provider-contract fixtures.
- Retire the old script only after feature parity and a tested migration.

See docs/modernisation.md and docs/e2e-validation.md. The legacy script and auth pin are intentionally unchanged in this first pass.
