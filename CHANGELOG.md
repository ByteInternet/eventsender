# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-07-30

### Added
- OpenTelemetry tracing support: `send_event` creates a producer span for every publish and injects the current trace context into the AMQP message headers, so consumers can continue the trace (see the amqpconsumer 1.8.0 counterpart)
- `opentelemetry-api` dependency. Without a configured OpenTelemetry backend all tracing calls are no-ops and behaviour is unchanged
- Tracing tests covering the no-op path, the header injection and the producer span attributes
- `pyproject.toml` with uv support, replacing the legacy packaging files
- Tracing section to the README

### Changed
- pika constraint from `==1.3.2` to `>=1.3.2,<1.4`
- Minimum Python version is now 3.9, enforced via `requires-python` so installs on older interpreters keep resolving 1.2.2
- Test runner from nose (unmaintained, broken on modern Python) to pytest; run with `uv run pytest tests`
- Test imports from the external `mock` package to the standard library `unittest.mock`

### Removed
- `setup.py`, `setup.cfg`, `MANIFEST.in`, `requirements.txt` and `tox.ini`, replaced by `pyproject.toml`
- nose and mock development dependencies
