# Contributing

Every change follows the same path, even a one-word fix.

1. Open an issue with a type label (`bug`, `enhancement` or `documentation`), an area label and a milestone.
2. Branch from an up-to-date `main`: `fix/<issue>-<slug>`, `feat/<issue>-<slug>`, `docs/<issue>-<slug>` or `chore/<slug>`.
3. Keep commits small, with an imperative subject: `Add`, `Fix`, `Update`, `Remove`, `Refactor`, `Test` or `Docs`.
4. Open a pull request that says `Closes #<issue>`.
5. Squash-merge once the `CI passed` check is green.

## Checks

CI only runs when someone starts it by hand, so these local checks are the gate. Run them before every push:

```
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
```

## Ground rules

- dotTide is read-only. A change that adds a write scope or calls an endpoint that changes anything won't be merged.
- No keys, tokens or filled-in profiles in the repo, the tests or the examples. Tests use made-up sites like `a.test`.
- New reports go in `src/dottide/report.py` so the MCP server, the CLI and the snapshot all share them. The server stays a thin wrapper.
- CI is one Linux job that runs only when started by hand. Keep it that way: no automatic triggers, no scheduled runs, no macOS runners, no matrix.
