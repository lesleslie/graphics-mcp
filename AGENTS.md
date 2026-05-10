# Repository Guidelines

## Project Structure & Module Organization

- `graphics_mcp/` contains the server package, including backend integrations, tool implementations, and image-processing helpers.
- `settings/` stores configuration defaults, and `tests/` should mirror the package structure for backend and tool coverage.
- `README.md` and `CLAUDE.md` should remain the primary operator-facing documentation; avoid hiding important behavior in ad hoc scripts.
- Generated artifacts in `dist/` should be treated as build output.

## Build, Test, and Development Commands

- `uv sync --group dev` installs development dependencies.
- Use the repo's documented local serve commands for stdio or HTTP smoke tests.
- `uv run pytest` executes the test suite.
- `uv run ruff check graphics_mcp tests` and `uv run ruff format graphics_mcp tests` cover linting and formatting.

## Coding Style & Naming Conventions

- Use explicit typing, validate file inputs, and keep tool handlers thin.
- Prefer backend-specific helpers beneath the package rather than packing logic into server entrypoints.
- Keep module names snake_case and user-facing tool responses structured and predictable.

## Testing Guidelines

- Add coverage for image transformations, path validation, and failure modes.
- Prefer fixture-based image assets and deterministic outputs where possible.

## Commit & Pull Request Guidelines

- Use focused commits such as `fix(convert): preserve alpha channel on resize`.
- PRs should mention backend impact, validation commands, and any output differences.

## Security & Configuration Tips

- Validate file paths and format conversions carefully.
- Never trust user-supplied paths or unchecked image metadata.
