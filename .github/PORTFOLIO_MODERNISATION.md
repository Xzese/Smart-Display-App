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
- Twelve focused tests passed; Xvfb open/navigation/close smoke check passed.

## Remaining
- Migrate settings, carousel, transitions, original visual design and QR authentication.
- Integrate the explicit outcomes from the local OAuth PR before updating its submodule pin.
- Verify live Graph/Weather API contracts and the intended Raspberry Pi display.
- Add package metadata, CI, complete provider fixtures and screenshots.
- Retire the old script only after feature parity and a tested migration.

See docs/modernisation.md. The legacy script and auth pin are intentionally unchanged in this first pass.
