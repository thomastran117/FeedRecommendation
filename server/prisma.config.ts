import "dotenv/config";
import { defineConfig } from "prisma/config";

export default defineConfig({
  // Kept only for app-side Prisma client generation.
  // Canonical schema definitions and migrations live in ../data-models/.
  schema: "prisma/schema.prisma",
  migrations: {
    path: "prisma/migrations",
  },
  datasource: {
    url: process.env["DATABASE_URL"],
  },
});
