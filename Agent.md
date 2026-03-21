# AGENT.md

## Core rules

- Follow strict TDD: write a failing test before implementation.
- Document all new or changed behavior in `docs/` using Markdown files.
- Prefer self-explanatory code over inline comments.
- Do not rely on comments in code as the primary form of documentation.

## Primary workflow

1. Write a failing test
2. Implement the minimal change to pass the test
3. Update or add documentation in `docs/`
4. Run tests
5. Refactor only if tests remain green

Do not implement features before writing tests.

## TDD requirements

- Every non-trivial change starts with a failing test.
- Every bug fix must include a regression test.
- Write the smallest test that captures the intended behavior.
- Implement the smallest code change needed to make the test pass.
- Do not add production code without a test that justified it.
- Do not claim completion without reporting test results.

## Documentation strategy

Documentation lives in a dedicated `docs/` folder as Markdown files.

The purpose of this documentation is:

- to give the agent stable project context
- to describe architecture and behavior outside the code
- to document decisions, flows, and conventions
- to provide a reference for future changes

Code should stay clean and readable without relying on comments.

## Documentation rules

- Add or update Markdown docs in `docs/` for all meaningful changes.
- Prefer updating an existing doc over creating duplicate docs.
- Create a new doc only when the topic does not already have a logical place.
- Keep docs concise, specific, and accurate.
- Write docs so another agent can use them as reference during future tasks.

## Documentation structure

Use `docs/` for project knowledge. Organize it with clear filenames.

Suggested structure:

- `docs/architecture.md` — system structure and design
- `docs/api.md` — endpoint behavior and contracts
- `docs/domain.md` — business rules and domain concepts
- `docs/testing.md` — testing conventions and fixtures
- `docs/decisions.md` — important technical decisions
- `docs/components/<name>.md` — detailed notes for specific modules or features
- `docs/features/<feature-name>.md` — feature-specific behavior and constraints

Follow the existing structure in the repository if one already exists.

## When documentation must be updated

Update `docs/` whenever you:

- add a new feature
- change behavior
- add or change an endpoint
- introduce a new service or domain rule
- change architecture or data flow
- add important constraints or assumptions
- make a decision future agents need to understand

Do not leave important behavior documented only in tests or code.

## Code documentation rules

- Avoid inline comments unless something is genuinely non-obvious.
- Avoid comment-heavy code.
- Prefer better naming and structure over explanatory comments.
- Use short module-level docstrings only when useful.
- Use function/class docstrings only for public interfaces or non-obvious behavior.
- Do not restate obvious code in comments.

## Module docstrings

A file may include a short top-level docstring describing:

- the purpose of the module
- its main responsibility
- related services or boundaries if helpful

Example:

```python
"""
User service layer for account creation, lookup, and status updates.
"""
```
