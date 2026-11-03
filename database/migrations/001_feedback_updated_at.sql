-- PostgreSQL: apply once before running the updated backend against an existing DB.
-- Nullable for legacy reviews; analysis falls back to created_at.
BEGIN;
ALTER TABLE feedback ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;
COMMIT;
