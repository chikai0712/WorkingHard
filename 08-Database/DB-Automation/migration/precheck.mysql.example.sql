-- MySQL pre-check example
SELECT DATABASE() AS current_database;
SELECT UTC_TIMESTAMP() AS current_time;
SHOW VARIABLES LIKE 'version';
-- Add free space / replication lag / metadata lock checks here
