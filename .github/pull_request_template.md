# Description

<!-- What does this change, and why? Link any related issue: "Closes #123" -->

## Type of change

- [ ] Bug fix
- [ ] New detection rule
- [ ] New feature
- [ ] Documentation
- [ ] Refactor / chore

## Checklist

- [ ] `uv run ruff check .` and `uv run ruff format --check .` pass
- [ ] `uv run mypy` passes (strict)
- [ ] `uv run pytest` passes, and new behaviour has tests
- [ ] `CHANGELOG.md` updated under `## [Unreleased]`
- [ ] Commits are signed off (`git commit -s`)

## For a new detection rule

- [ ] Positive samples (must match) added as tests
- [ ] Negative near-miss samples (must NOT match) added as tests
- [ ] Pattern has **no nested quantifiers** and **bounded repetition** (ReDoS safety)
- [ ] All sample values are fake and provably dead

## Security

- [ ] This change introduces **no network calls**
- [ ] No secret is printed unmasked, including in error messages and tracebacks
- [ ] No real credentials appear in the diff, tests, or commit messages
