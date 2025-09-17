-- Migration: 001_initial_schema.sql
-- Description: Initial database schema with pgvector support
-- Applied: This migration has already been applied during schema creation
-- Version: 1.0.0

-- This file serves as a record of the initial schema creation
-- The actual schema was created from database/schema.sql

-- To verify this migration was applied, check:
-- SELECT * FROM schema_version WHERE version = '1.0.0';

-- Migration rollback (if needed):
-- DROP SCHEMA public CASCADE;
-- CREATE SCHEMA public;
-- GRANT ALL ON SCHEMA public TO jianbinfang;
-- GRANT ALL ON SCHEMA public TO public;