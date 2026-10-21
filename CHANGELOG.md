# Changelog

## 0.2.0 - 2026-10-21

- Installable with `pip install` / `pipx install`; adds the `ue` command and `python -m usage_engineer`.
- State moves to `~/.usage-engineer` (override with `UE_STATE_DIR`); older checkouts keep using
  their existing `state/` folder so recorded applies can still be rolled back.
- Benchmark run records go to the state directory instead of the package folder.
- CI on Linux, macOS and Windows.
- Fix: `%HOME%` redaction now also covers the resolved and Windows 8.3 short spellings of the
  home path (for example `C:\Users\RUNNER~1`), which previously leaked into reports.

## 0.1.0 - 2026-09-20

- First version: `audit`, `summarize-log`, `prepare-context`, `map`, `instructions`, `compare`,
  `apply-profile` / `rollback`, `bench`, `doctor`, `selftest` (25 deterministic tests).
