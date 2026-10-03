# Portfolio modernisation

Placeholder for a focused modernisation of the Smart Display application.

## Scope
- Make startup safe when credentials or optional integrations are not configured.
- Separate UI, runtime state, configuration, authentication and external providers.
- Move weather and Instagram network work off the Tkinter UI event loop and add bounded timeouts.
- Preserve the last successful values and expose clear offline, stale and authentication-required states.
- Add a deterministic offline/demo mode with bundled fictional data.
- Improve layout scaling while retaining the original wide-display use case.
- Add automated tests for first-run, slow/offline providers, authentication cancellation and shutdown.
- Review the Facebook/Instagram Graph API version and update it through a tested, configurable integration.
- Refresh the README with a quick-start demo, architecture notes and real screenshots.

## Portfolio outcome
Show a clear before-and-after case study: the original functional prototype evolved into a modular, resilient and testable display application.

No implementation is included in this placeholder PR.