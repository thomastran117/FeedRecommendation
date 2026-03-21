import { PrismaPg } from '@prisma/adapter-pg';
import { PrismaClient } from '../generated/client.js';

const globalForPrisma = globalThis;

const adapter = new PrismaPg({ connectionString: process.env.DATABASE_URL || "postgresql://postgres:postgres@localhost:5432/expressapp"});

const prisma =
  globalForPrisma.prisma ||
  new PrismaClient({
    adapter,
    log: ['query', 'error', 'warn'],
  });

if (process.env.NODE_ENV !== 'production') {
  globalForPrisma.prisma = prisma;
}

export default prisma;