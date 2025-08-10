-- Seed test users for registered_users and pending_users tables
-- Database: SQLite (file: src\database\database.db)
--
-- Usage (PowerShell):
--   1) Ensure sqlite3 is available in your PATH.
--   2) From the repository root, run:
--        sqlite3 .\src\database\database.db ".read .\src\database\seeds\seed_test_users.sql"
--
-- Notes:
-- - INSERT OR IGNORE makes this script idempotent: if the telegram_id/username/phone already exist,
--   the insert will be skipped to avoid unique constraint violations.
-- - Adjust the sample data as needed. The chosen telegram_id values are in a high test range to avoid collisions.

BEGIN TRANSACTION;

-- Registered users (several)
INSERT OR IGNORE INTO registered_users (
    telegram_id,
    username,
    first_name,
    last_name,
    email,
    phone,
    role
) VALUES
    (999000001, 'test_registered', 'Test',    'User',  'test.registered@example.com', '+999000001', 'user'),
    (999000003, 'qa_alice',       'Alice',   'Roe',   'alice.qa@example.com',         '+999000003', 'user'),
    (999000004, 'qa_bob',         'Bob',     'Smith', 'bob.qa@example.com',           '+999000004', 'manager'),
    (999000005, 'qa_charlie',     'Charlie', NULL,    'charlie.qa@example.com',       '+999000005', 'user'),
    (999000006, 'qa_dina',        'Dina',    'Swift', NULL,                            '+999000006', 'admin');

-- Pending users (several)
INSERT OR IGNORE INTO pending_users (
    telegram_id,
    username,
    first_name,
    last_name,
    email,
    phone,
    from_whom
) VALUES
    (999000002, 'test_pending', 'Pending', 'User', 'test.pending@example.com', '+999000002', 'qa_seed'),
    (999000007, 'qa_erin',      'Erin',    'Lee',  'erin.qa@example.com',      '+999000007', 'referral_alice'),
    (999000008, 'qa_frank',     'Frank',   NULL,   NULL,                        '+999000008', 'web_form'),
    (999000009, 'qa_grace',     'Grace',   'Kim',  NULL,                        '+999000009', 'walk_in'),
    (999000010, 'qa_henry',     'Henry',   'Ng',   'henry.qa@example.com',      '+999000010', 'event_booth');

COMMIT;

-- Optional cleanup (uncomment to remove the test rows):
-- DELETE FROM registered_users WHERE telegram_id IN (999000001, 999000003, 999000004, 999000005, 999000006);
-- DELETE FROM pending_users    WHERE telegram_id IN (999000002, 999000007, 999000008, 999000009, 999000010);