-- Membership: a profile worth having, and identity that survives a reinstall.
alter table users add column if not exists display_name text;
alter table users add column if not exists email        text;      -- restore hatch, not auth
alter table users add column if not exists goal         text;      -- why they're here; drives copy
alter table users add column if not exists restore_code text;      -- short code to recover on a new device
create unique index if not exists users_email_idx        on users (lower(email)) where email is not null;
create unique index if not exists users_restore_code_idx on users (restore_code) where restore_code is not null;

-- which line was practised, not just which sound. "You keep struggling with this sentence"
-- is more actionable than "your numbers are 87", and adaptive resurfacing needs it.
alter table attempts add column if not exists line_ref text;
create index if not exists attempts_line_idx on attempts (user_id, line_ref);
