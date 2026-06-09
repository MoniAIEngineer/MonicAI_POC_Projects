-- ─────────────────────────────────────────────
-- RentScout — Supabase schema
-- Run in the Supabase SQL editor.
-- ─────────────────────────────────────────────

-- Users
create table if not exists users (
    id uuid primary key default gen_random_uuid(),
    email text unique not null,
    password_hash text not null,
    telegram_id text,
    created_at timestamptz default now()
);

-- Saved search preferences
create table if not exists searches (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references users(id) on delete cascade,
    city text,
    max_rent numeric,
    min_rooms numeric,
    search_url text,
    created_at timestamptz default now()
);

-- Scraped listings
create table if not exists listings (
    id uuid primary key default gen_random_uuid(),
    external_id text unique,          -- portal listing id, for de-duplication
    title text,
    address text,
    city text,
    rent numeric,
    rooms numeric,
    size_sqm numeric,
    url text,
    source text default 'immowelt',
    scraped_at timestamptz default now()
);

-- De-duplication / lookup index
create index if not exists listings_external_idx on listings (external_id);
create index if not exists listings_city_rent_idx on listings (city, rent);
