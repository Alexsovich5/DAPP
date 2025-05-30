-- Initialize Dinner1 Database
-- This file runs when the PostgreSQL container starts for the first time

-- Create the database (already created by POSTGRES_DB env var)
-- CREATE DATABASE dinner1;

-- Set timezone
SET timezone = 'UTC';

-- Create any extensions we might need
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Log initialization
SELECT 'Dinner1 database initialized successfully' as message;