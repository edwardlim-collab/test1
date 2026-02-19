# CLAUDE.md

This file provides guidance for AI assistants (Claude and others) working in this repository.

## Repository Status

This repository is currently **empty** — no source code, framework, or tooling has been committed yet. This file serves as a foundational guide to be updated as the project evolves.

---

## Git Workflow

### Branch Naming
- Feature branches: `feature/<short-description>`
- Bug fixes: `fix/<short-description>`
- Claude-driven branches: `claude/<task-id>` (auto-generated)

### Commit Messages
Use the imperative mood and keep the subject line under 72 characters:
```
Add user authentication module
Fix null pointer in payment handler
Refactor database connection pooling
```

For multi-line commits:
```
Short summary (≤72 chars)

Optional longer explanation of why the change was made,
what problem it solves, and any trade-offs considered.
```

### Push Protocol
- Always push with tracking: `git push -u origin <branch-name>`
- Never force-push to `main` or `master`
- On network failure, retry up to 4 times with exponential backoff (2s, 4s, 8s, 16s)

### Pull Requests
- Keep PRs focused — one logical change per PR
- Include a summary of what changed and why
- Reference related issues when applicable

---

## Development Principles

### Code Quality
- Prefer clarity over cleverness; readable code is maintainable code
- Keep functions small and single-purpose
- Avoid premature abstraction — add helpers only when the same logic appears in 3+ places
- Delete unused code rather than commenting it out

### Error Handling
- Validate at system boundaries (user input, external APIs, file I/O)
- Trust internal framework guarantees; avoid redundant defensive checks
- Propagate errors explicitly rather than swallowing them silently

### Testing
- Write tests for public interfaces, not implementation details
- Each test should verify one behavior
- Tests should be deterministic and not depend on external services unless integration tests

### Security
- Never commit secrets, credentials, or API keys — use environment variables or a secrets manager
- Sanitize all user input before using it in queries, commands, or rendering
- Follow OWASP Top 10 guidelines; avoid SQL injection, XSS, command injection, etc.

---

## AI Assistant Guidelines

When working in this repository, Claude and other AI assistants should:

### Before Making Changes
- Read relevant files before editing them
- Understand the existing pattern before introducing a new one
- Verify that a requested change does not already exist

### Scope of Changes
- Make only the changes directly requested or clearly necessary
- Do not refactor surrounding code unless asked
- Do not add docstrings, comments, or type annotations to code that was not changed
- Do not add feature flags, backwards-compatibility shims, or extra configurability unless asked

### File Operations
- Prefer editing existing files over creating new ones
- Never create documentation files (README, CLAUDE.md) unless explicitly requested
- Use atomic, focused edits rather than rewriting entire files

### Communication
- Output explanations as plain text responses, not as shell `echo` commands or code comments
- Keep responses concise and factual; avoid excessive praise or filler phrases
- When uncertain, investigate first rather than assuming

---

## Setting Up a New Project

When a tech stack is chosen, update this file with:

1. **Language & Runtime** — e.g., Node.js 20, Python 3.12, Go 1.22
2. **Framework** — e.g., Express, FastAPI, Gin
3. **Install dependencies** — e.g., `npm install`, `pip install -e ".[dev]"`
4. **Build** — e.g., `npm run build`, `make build`
5. **Run locally** — e.g., `npm start`, `python -m app`
6. **Run tests** — e.g., `npm test`, `pytest`, `go test ./...`
7. **Lint / format** — e.g., `npm run lint`, `ruff check .`, `gofmt`
8. **Environment variables** — list required env vars and where to find sample values

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| *(none defined yet)* | | |

Update this table as environment variables are introduced.

---

## Project Structure (To Be Defined)

Once source code is added, document the directory layout here. Example format:

```
src/
  controllers/   # Request handlers
  services/      # Business logic
  models/        # Data models / ORM schemas
  utils/         # Shared utilities
tests/
  unit/
  integration/
docs/
```

---

*Last updated: 2026-02-19 — initial scaffold for empty repository.*
