# Contributing

Every change follows the same path, even a one-word fix.

1. Open an issue with a type label (`bug`, `enhancement` or `documentation`), an area label and a milestone.
2. Branch from an up-to-date `main`: `fix/<issue>-<slug>`, `feat/<issue>-<slug>`, `docs/<issue>-<slug>` or `chore/<slug>`.
3. Keep commits small, with an imperative subject: `Add`, `Fix`, `Update`, `Remove`, `Refactor`, `Test` or `Docs`.
4. Open a pull request that says `Closes #<issue>`.
5. Squash-merge once the `CI passed` check is green.

## Working from source

```
git clone https://github.com/dotbrainhq/dottide.git
cd dottide
uv sync
uv run dottide sites
```

`uv run dottide` runs your checkout instead of the published package.

## Releases

1. Close the milestone's issues, then bump the version in `pyproject.toml` and `CHANGELOG.md` in a pull request.
2. After it merges, tag `main` and push the tag. The Release job in GitHub Actions tests, builds and publishes to PyPI through trusted publishing, so no token is stored anywhere.

```
git switch main && git pull && git tag vX.Y.Z && git push origin vX.Y.Z
gh release create vX.Y.Z --generate-notes
```

## Checks

Run these before opening a pull request:

```
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
```

## Ground rules

- dotTide is read-only. A change that adds a write scope or calls an endpoint that changes anything won't be merged.
- No keys, tokens or filled-in profiles in the repo, the tests or the examples. Tests use made-up sites like `a.test`.
- New reports go in `src/dottide/report.py` so the MCP server, the CLI and the snapshot all share them. The server stays a thin wrapper.
- CI runs one Linux job on pull requests only. Keep it that way: no scheduled runs, no macOS runners, no matrix.
