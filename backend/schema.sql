-- Papaya schema. Three tables on purpose (PLAN.md Step 1).
-- A unit is a document, read whole, written once -> jsonb, not 7 normalised tables.
-- Streaks, XP and per-sound meters are all GROUP BY over attempts -> no progress/streak/xp tables.

create table if not exists units (
    scenario_id text not null,
    locale      text not null,              -- 'global' for core content, 'en-AU' etc for locale packs
    data        jsonb not null,
    updated_at  timestamptz not null default now(),
    primary key (scenario_id, locale)
);

-- resolution is: global core UNION locale pack, pack wins on shared scenario_id (CLAUDE.md s6)
create index if not exists units_locale_idx on units (locale);

create table if not exists users (
    id         uuid primary key,            -- device-generated, no auth until there's money
    locale     text not null default 'en-AU',
    tz         text not null default 'Australia/Sydney',  -- streak day boundaries; this population travels
    created_at timestamptz not null default now()
);

-- The product's brain. One row per scored attempt.
create table if not exists attempts (
    id             bigserial primary key,
    user_id        uuid not null references users(id),
    scenario_id    text not null,
    stage          text not null,           -- 'shadow' | 'guided_roleplay' | 'free_roleplay' | 'listening'
    sound_target   text,                    -- 'final_consonants', 'th', ... null for non-pronunciation stages
    scoring_method text,                    -- 'phoneme' | 'minimal_pair'  (Step 0: /th/ can't use phoneme)
    raw_score      real,                    -- what the vendor returned
    ceiling        real,                    -- what a perfect native take scores for THIS phoneme (Step 0)
    score          real,                    -- raw_score/ceiling*100, clamped. THIS is what a learner sees.
    seconds_spoken real not null default 0, -- streak currency: minutes spoken, not lessons tapped
    raw            jsonb,                   -- full vendor response, for debugging and re-scoring
    created_at     timestamptz not null default now()
);

create index if not exists attempts_user_time_idx  on attempts (user_id, created_at desc);
create index if not exists attempts_user_sound_idx on attempts (user_id, sound_target);

-- Scenarios the locale pack drops from the core registry: Thailand-resident content that makes no
-- sense abroad (BTS/MRT, songthaew, 90-day reporting). Without this, an en-AU learner is offered
-- lessons about the Bangkok Skytrain.
create table if not exists locale_drops (
    locale      text not null,
    scenario_id text not null,
    primary key (locale, scenario_id)
);
