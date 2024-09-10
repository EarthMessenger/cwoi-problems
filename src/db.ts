import { createPool } from '@vercel/postgres';

export const pgPool = createPool({
  connectionString: import.meta.env.POSTGRES_URL,
});