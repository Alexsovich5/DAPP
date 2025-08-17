-- Initialize test database with proper configuration
-- This script runs when the PostgreSQL container starts

-- Create additional test databases if needed
CREATE DATABASE testdb_integration;
CREATE DATABASE testdb_performance;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE testdb TO testuser;
GRANT ALL PRIVILEGES ON DATABASE testdb_integration TO testuser;
GRANT ALL PRIVILEGES ON DATABASE testdb_performance TO testuser;

-- Enable extensions that might be needed
\c testdb;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

\c testdb_integration;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

\c testdb_performance;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create test-specific schemas or configurations if needed
\c testdb;
CREATE SCHEMA IF NOT EXISTS test_schema;
GRANT ALL ON SCHEMA test_schema TO testuser;