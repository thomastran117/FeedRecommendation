# Data Models

`data-models/` is the source of truth for the database layer.

## Rules

- Define canonical database schemas in `data-models/schema/`.
- Author canonical SQL migrations in `data-models/migrations/`.
- Keep database reference docs in `data-models/docs/`.
- Application folders may keep ORM client mappings for querying, but they must not own schema definitions or migration history.
- When the schema changes, update both `data-models/docs/` and the project docs in `docs/`.

## Layout

- `schema/` — canonical schema definitions
- `migrations/` — ordered SQL migrations
- `docs/` — storage-model reference documentation
