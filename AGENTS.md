# Repository Guidelines

## Project Structure & Module Organization
This repository currently contains the product brief in `GUIDE.MD` and no implementation yet. Keep the root clean and add code under a dedicated app directory such as `src/` or `app/`. Place reusable logic in feature-focused modules, for example `src/classification/`, `src/reply/`, and `src/routing/`. Store sample transcripts, mock APIs, and prompt fixtures in `data/` or `fixtures/`. Put automated tests in `tests/`, mirroring the source layout.

## Build, Test, and Development Commands
Document all runnable commands in `README.md` once the stack is chosen. Prefer a small, repeatable set:

- `make dev` or `npm run dev`: start the local app or API server.
- `make test` or `npm test`: run the automated test suite.
- `make lint` or `npm run lint`: run formatting and static checks.
- `make build` or `npm run build`: produce a production-ready bundle when applicable.

If you do not use `make`, keep command names consistent across scripts.

## Coding Style & Naming Conventions
Use 2 spaces for front-end files and JSON/YAML, or 4 spaces for Python if this becomes a Python solution. Follow the formatter and linter native to the chosen stack, such as `prettier` and `eslint`, or `black` and `ruff`. Use `camelCase` for variables and functions in JavaScript/TypeScript, `snake_case` in Python, and `PascalCase` for React components or class names. Name files by responsibility, for example `message_router.ts` or `test_message_router.py`.

## Testing Guidelines
Add tests for each user-facing capability: classification, reply generation, routing, and any escalation logic. Keep test files under `tests/` with names like `test_routing.py` or `message-router.test.ts`. Prefer deterministic fixtures over ad hoc prompts so outputs can be asserted reliably. Include at least one edge-case test for urgent escalation and one for unsupported input.

## Commit & Pull Request Guidelines
Git history is not available in this workspace, so no existing commit convention can be inferred. Use short, imperative commit subjects such as `feat: add triage classifier` or `fix: handle missing transcript`. Keep pull requests focused and include:

- a brief summary of scope
- setup and test evidence
- screenshots or sample request/response output for UI or API changes
- notes on tradeoffs, mocks, and AI usage if relevant

## Security & Configuration Tips
Do not commit secrets, API keys, or patient-like data. Keep environment-specific values in `.env` files excluded from version control, and sanitize all sample transcripts before storing them in the repository.
