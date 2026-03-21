# Prisma Consumer Notes

`server/prisma/` is no longer the source of truth for database structure.

Use the top-level `data-models/` folder for:
- canonical schema definitions
- canonical SQL migrations
- database structure documentation

Files in this folder are application-side Prisma artifacts only.
Do not add new schema definitions or new migration ownership here.

Existing files under `server/prisma/migrations/` are legacy from before the database-definition move.
