create table if not exists public.complaints (
 id uuid primary key,
 created_at timestamptz not null default now(),
 location text not null,
 description text not null,
 status text not null default 'Pending' check (status in ('Pending','In Progress','Resolved')),
 photo_path text,
 latitude double precision,
 longitude double precision
);
alter table public.complaints enable row level security;
-- In Supabase Storage create a PRIVATE bucket named complaint-photos.

-- If you already created the old table, also run:
alter table public.complaints add column if not exists latitude double precision;
alter table public.complaints add column if not exists longitude double precision;
