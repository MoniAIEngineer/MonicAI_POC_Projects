-- ─────────────────────────────────────────────
-- BehördenBot — Supabase schema
-- Run in the Supabase SQL editor.
-- Requires the pgvector extension.
-- ─────────────────────────────────────────────

-- Enable pgvector
create extension if not exists vector;

-- Users
create table if not exists users (
    id uuid primary key default gen_random_uuid(),
    telegram_id text unique,
    email text,
    subscription_status text default 'free',
    language text default 'de',
    created_at timestamptz default now()
);

-- Processed letters
create table if not exists letters (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references users(id) on delete cascade,
    raw_text text,
    explanation text,
    created_at timestamptz default now()
);

-- Knowledge base (embedded chunks for RAG)
create table if not exists letter_templates (
    id uuid primary key default gen_random_uuid(),
    title text,
    content text,
    embedding vector(1536),
    created_at timestamptz default now()
);

-- Vector similarity index
create index if not exists letter_templates_embedding_idx
    on letter_templates
    using ivfflat (embedding vector_cosine_ops)
    with (lists = 100);
