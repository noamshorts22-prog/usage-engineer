# Usage-engineer workflow (opt-in, additive)

This project uses the local `usage-engineer` helpers (no network, no credentials).
Requirements, acceptance criteria, security rules and required tests are NOT reduced by this file.

- Prefer a task context pack at the start of non-trivial work:
  `python <tool>\ue.py prepare-context --project . --request-file <request.md> --verify "<check command>"`
  Treat it as a starting point; widen inspection whenever evidence requires it.
- For large command output, do not paste the whole log into the conversation:
  `python <tool>\ue.py summarize-log --file <log>` keeps every failure/error line plus the full
  original file path. Always keep that path reachable when reporting results.
- If the same command/action fails twice with identical input, change approach instead of repeating.
- Before resuming from an older map/checkpoint:
  `python <tool>\ue.py map check --project . --map <map.json>` - if STALE, re-read the listed files.
- Report actual command results; never describe an unrun check as passing.
