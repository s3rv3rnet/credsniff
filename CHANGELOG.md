# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Project scaffolding: `src/` layout, uv-managed dependencies with a committed
  `uv.lock`, and PEP 621 metadata.
- Quality tooling wired from the start: `ruff` (including bandit security rules),
  `mypy --strict`, `pytest`, and coverage configuration.
- `py.typed` marker so downstream type checkers honour our annotations.
- Project governance: README, security policy, contributing guide, code of conduct,
  issue and pull request templates.

[Unreleased]: https://github.com/s3rv3rnet/credsniff/commits/main
