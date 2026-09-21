CREATE ROLE analyst_readonly LOGIN PASSWORD 'ReadOnly2026';

GRANT CONNECT ON DATABASE analytics TO analyst_readonly;
GRANT USAGE ON SCHEMA public TO analyst_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analyst_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO analyst_readonly;

ALTER ROLE analyst_readonly SET default_transaction_read_only = on;
ALTER ROLE analyst_readonly SET statement_timeout = '15s';