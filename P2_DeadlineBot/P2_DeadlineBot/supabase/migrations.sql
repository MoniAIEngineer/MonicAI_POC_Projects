-- ─────────────────────────────────────────────
-- DeadlineBot — Supabase schema
-- Run in the Supabase SQL editor.
-- (Shared project with other portfolio bots — table names namespaced.)
-- ─────────────────────────────────────────────

-- Users
create table if not exists users (
    id uuid primary key default gen_random_uuid(),
    telegram_id text unique,
    email text,
    language text default 'de',
    created_at timestamptz default now()
);

-- Deadlines
create table if not exists deadlines (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references users(id) on delete cascade,
    title text not null,
    raw_input text,
    due_at timestamptz not null,
    reminder_sent boolean default false,
    source text default 'telegram',   -- 'telegram' | 'voice' | 'web'
    created_at timestamptz default now()
);

-- Index for the reminder workflow to query upcoming, unsent deadlines
create index if not exists deadlines_due_idx
    on deadlines (due_at)
    where reminder_sent = false;
