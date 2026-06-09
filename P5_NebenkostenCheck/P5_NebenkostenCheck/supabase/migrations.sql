-- ─────────────────────────────────────────────
-- NebenkostenCheck — Supabase schema
-- Run in the Supabase SQL editor.
-- ─────────────────────────────────────────────

-- Email capture (free beta gate) + customers
create table if not exists users (
    id uuid primary key default gen_random_uuid(),
    email text unique not null,
    is_paid boolean default false,
    created_at timestamptz default now()
);

-- Analysis sessions (roadmap: move from in-memory to here)
create table if not exists analyses (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references users(id) on delete set null,
    filename text,
    status text default 'pending',     -- pending | complete | failed
    total_charges numeric,
    flagged_count integer default 0,
    result jsonb,                       -- structured analysis output
    created_at timestamptz default now()
);

-- Payment records (Dodo)
create table if not exists payments (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references users(id) on delete set null,
    dodo_payment_id text unique,
    amount numeric default 19,
    currency text default 'EUR',
    status text default 'pending',      -- pending | paid | refunded
    created_at timestamptz default now()
);

create index if not exists analyses_user_idx on analyses (user_id);
create index if not exists payments_dodo_idx on payments (dodo_payment_id);
