# NBA Connections – Supabase Integration Guide

> **Purpose**
> This document captures every touch‑point between the code‑base and Supabase so the backend can be recreated (or swapped for another store such as Google Sheets) without reverse‑engineering the project again.

---

## 1. Architectural Overview

```mermaid
flowchart TD
    subgraph Backend (Python)
        TG[theme_generator.py] -->|insert| TH(themes)
        TV[theme_validator.py] -->|update| TH
        PG[puzzle_generator.py] -->|read| TH
        PM[puzzle_manager.py] -->|insert/update| PU(puzzles)
        FA[*fetch_*.py] -->|upsert| CoreTables[(core stat tables)]
        Q[*queries/*.py] -->|insert| NT(new_themes) & TP(theme_players)
    end

    subgraph Database (Supabase /Postgres)
        TH(themes) --- NT(new_themes)
        NT --- TP(theme_players)
        PU(puzzles) --- EP(eligible_puzzles)
        CoreTables --> AllOther[all_time_leaders, league_leaders, …]
    end

    subgraph Frontend (Next .js)
        Game[src/app/nba-connections-game.tsx] -->|read puzzle of day| PU
    end
```

* **Backend** populates and maintains data via the Supabase **Service Key**.
* **Frontend** consumes *read‑only* data using the **Anon Key**.

---

## 2. Environment Variables

| Variable                                | Location(s)                        | Meaning                                       |
| --------------------------------------- | ---------------------------------- | --------------------------------------------- |
| `NEXT_PUBLIC_SUPABASE_URL`              | root `.env`, `src/lib/supabase.ts` | Project URL for client‑side reads             |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY`         | root `.env`                        | Public key with RLS applied                   |
| `NEXT_PUBLIC_SUPABASE_SERVICE_KEY`      | (*optional*) root `.env`           | Service key – rarely exposed client side      |
| `SUPABASE_URL`                          | `backend/.env`                     | Service URL for Python scripts                |
| `SUPABASE_KEY` / `SUPABASE_SERVICE_KEY` | `backend/.env`                     | **Service role** key for data‑loading scripts |

> ℹ️ Keys are loaded via **dotenv** then passed to `supabase.create_client()` in **backend/supabase\_client.py** and `src/lib/supabase.ts`.

---

## 3. Supabase Client Factories

### Backend (full access)

```python
from supabase import create_client
supabase = create_client(os.getenv("SUPABASE_URL"),
                         os.getenv("SUPABASE_SERVICE_KEY"))
```

*Defined in* `backend/supabase_client.py` and imported everywhere in *backend/*.
Grants INSERT/UPDATE/UPSERT on all tables.

### Frontend (read‑only)

```ts
import { createClient } from "@supabase/supabase-js";
export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);
```

*Defined in* `src/lib/supabase.ts`. Used inside `nba-connections-game.tsx` to fetch the daily puzzle.

---

## 4. Database Schemas

All DDL lives under **`backend/schemas/`**.  The order below respects foreign‑key dependencies:

| File                   | Table(s)                                                    | Key Columns                                     | Used by                     |
| ---------------------- | ----------------------------------------------------------- | ----------------------------------------------- | --------------------------- |
| `themes.sql`           | `themes`                                                    | `theme_id`, `used_in_puzzle`, `validated_state` | Theme pipeline              |
| `new_themes.sql`       | `new_themes`                                                | `theme_id`, `used_in_puzzle`                    | SQL‑generated themes        |
| `theme_players.sql`    | `theme_players`                                             | (`theme_id`, `player_name`) PK                  | Links themes → players      |
| `puzzles.sql`          | `puzzles`                                                   | `date` (unique), `groups` (JSON)                | Frontend & daily API        |
| `eligible_puzzles.sql` | `eligible_puzzles`                                          | `is_verified`, `add_to_puzzles`                 | Staging area before publish |
| *Core stat tables*     | `all_time_leaders`, `league_leaders`, `draft_history`, etc. | domain‑specific                                 | Data ingest scripts         |

> **Indexes** are pre‑declared in the SQL to ensure fetch speed (e.g., `idx_puzzles_date_key`).

### Relationships (logical)

* **themes.theme\_id** ↔ **theme\_players.theme\_id** (1‑many)
* **new\_themes.theme\_id** ↔ **theme\_players.theme\_id** (alt source)
* **puzzles.date** is queried with `eq('date', YYYY‑MM‑DD)` for “puzzle of the day”.

---

## 5. Data Ingestion & Maintenance Scripts

### 5.1 NBA Stats Fetchers – `backend/fetch_nba_api/`

Each script pulls from `nba_api` endpoint(s) then **upserts** into one table.  Run ad‑hoc or on a schedule.

| Script                        | Source endpoint       | Target table                     |
| ----------------------------- | --------------------- | -------------------------------- |
| `fetch_all_time_leaders.py`   | `alltimeleadersgrids` | `all_time_leaders`               |
| `fetch_common_player_info.py` | `commonplayerinfo`    | `common_player_info`             |
| `fetch_common_team_roster.py` | `commonteamroster`    | `common_team_roster` (+ coaches) |
| …                             | …                     | …                                |

> All fetchers handle rate‑limits (retry & back‑off) and store logs in `backend/fetch_nba_api/logs/`.

### 5.2 Theme & Puzzle Pipeline

1. **`theme_generator.py`** – uses GPT‑4o to propose themes → `themes` (insert).
2. **`theme_validator.py`** – validates with Search API → sets `validated_state = true`.
3. **`puzzle_generator.py`** – loads *validated* themes, builds 4‑theme puzzles, writes JSON locally.
4. **`puzzle_manager.py`** – validates JSON, assigns calendar dates, inserts into `puzzles`, and flips `used_in_puzzle` flags.

### 5.3 SQL‑Driven Theme Builders – `backend/queries/`

These scripts generate *structured* themes (e.g., “All‑NBA First Team 2010”) by reading core tables and writing to **`new_themes`**/**`theme_players`**.

---

## 6. Frontend Usage Pattern

File **`src/app/nba-connections-game.tsx`** performs the only read from the client:

```ts
supabase
 .from('puzzles')
 .select('*')
 .eq('date', formattedDate) // YYYY‑MM‑DD in local time
 .single();
```

Returns a row whose `groups` column is a JSONB array with words, theme, color & emoji.  The game logic is entirely offline after that.

> **Security note:** All other tables are service‑role only.  Make sure RLS leaves them private.

---

## 7. Local Development & Migration

1. **Spin up the database** (via Supabase Cloud or `supabase start`).
2. `psql` → run every file in **`backend/schemas/`** (order above). Supabase CLI migrations work too.
3. Create `.env`/`.env.local` and populate keys.
4. Run fetchers to seed core tables (can be selective).
5. Run *theme* & *puzzle* pipelines; verify `puzzles` populated.
6. Start Next.js: `npm run dev`.

---

## 8. Daily Ops

| Task                          | Command                                                    | Schedule suggestion                    |
| ----------------------------- | ---------------------------------------------------------- | -------------------------------------- |
| Refresh core stat tables      | `python backend/fetch_nba_api/*.py`                        | Weekly (off‑season) / nightly (season) |
| Generate new validated themes | `python backend/theme_generator.py` + `theme_validator.py` | Ad‑hoc when stock < 100                |
| Build tomorrow’s puzzle       | `python backend/puzzle_manager.py`                         | Daily cron after 00:05 ET              |

---

## 9. Mapping Tables → Google Sheets (Future Work)

| Postgres Table                | Suggested Sheet                                                                                     | Notes                                                           |
| ----------------------------- | --------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| `puzzles`                     | *Puzzles*                                                                                           | Each row a puzzle; `groups` can be JSON in a cell or 16 columns |
| `themes`                      | *Themes‑Validated*                                                                                  | Flatten `words[0‑3]` into columns                               |
| `new_themes`, `theme_players` | *Themes‑SQL* / *Theme Players*                                                                      | Retain `theme_id` as UID                                        |
| `all_time_leaders` etc.       | External – keep in CSV/BigQuery; not necessary in Sheets unless you plan to regenerate themes there |                                                                 |

A simple Apps Script or Make.com scenario can replicate the read/query patterns (`get puzzle where date = TODAY()`).

---

## 10. Quick Reference – Supabase Calls

```text
Insert rows : .insert(record).execute()
Upsert rows : .upsert(record).execute()
Select rows : .select('*').eq(column, value).execute()
Update rows : .update({'col': val}).eq(column, value).execute()
Delete rows : .delete().eq(column,value).execute()
```

All scripts follow this pattern – search for `supabase.table(` to see concrete usages.

---

## 11. Useful SQL Helpers

```sql
-- ===== NBA Connections – Full Production DDL (snapshot 2025‑06‑26) =====

create table public.all_time_leaders (
  id bigint generated by default as identity not null,
  player_id integer not null,
  player_name text not null,
  stat_value numeric not null,
  stat_rank integer not null,
  stat_category text not null,
  constraint all_time_leaders_pkey primary key (id),
  constraint all_time_leaders_player_id_stat_category_key unique (player_id, stat_category)
);
create index if not exists idx_all_time_leaders_player_id on public.all_time_leaders using btree (player_id);
create index if not exists idx_all_time_leaders_stat_category on public.all_time_leaders using btree (stat_category);

create table public.common_player_info (
  player_id integer not null,
  first_name character varying null,
  last_name character varying null,
  display_first_last character varying null,
  display_last_comma_first character varying null,
  display_fi_last character varying null,
  player_slug character varying null,
  birthdate date null,
  school character varying null,
  country character varying null,
  last_affiliation character varying null,
  height character varying null,
  weight integer null,
  season_exp integer null,
  jersey character varying null,
  position character varying null,
  roster_status boolean null,
  team_id integer null,
  team_name character varying null,
  team_abbreviation character varying null,
  team_code character varying null,
  team_city character varying null,
  playercode character varying null,
  from_year integer null,
  to_year integer null,
  dleague_flag boolean null,
  nba_flag boolean null,
  games_played_flag boolean null,
  draft_year integer null,
  draft_round integer null,
  draft_number integer null,
  constraint common_player_info_pkey primary key (player_id)
);

create table public.common_team_roster (
  team_id integer not null,
  team_name text null,
  season text not null,
  leagueid text null,
  player text null,
  player_slug text null,
  num text null,
  position text null,
  height text null,
  weight text null,
  birth_date text null,
  age integer null,
  exp text null,
  school text null,
  player_id integer not null,
  how_acquired text null,
  nickname text null,
  constraint common_team_roster_pkey primary key (team_id, player_id, season)
);
create index if not exists idx_common_team_roster_player_id on public.common_team_roster using btree (player_id);
create index if not exists idx_common_team_roster_season on public.common_team_roster using btree (season);
create index if not exists idx_common_team_roster_team_id on public.common_team_roster using btree (team_id);

create table public.common_team_roster_coaches (
  team_id integer not null,
  team_name text null,
  season text not null,
  coach_id integer not null,
  first_name text null,
  last_name text null,
  coach_name text null,
  is_assistant boolean null,
  coach_type text null,
  sort_sequence integer null,
  constraint common_team_roster_coaches_pkey primary key (team_id, coach_id, season)
);
create index if not exists idx_common_team_roster_coaches_coach_id on public.common_team_roster_coaches using btree (coach_id);
create index if not exists idx_common_team_roster_coaches_season on public.common_team_roster_coaches using btree (season);
create index if not exists idx_common_team_roster_coaches_team_id on public.common_team_roster_coaches using btree (team_id);

create table public.draft_history (
  person_id integer not null,
  player_name text null,
  season integer not null,
  round_number integer null,
  round_pick integer null,
  overall_pick integer not null,
  draft_type text null,
  team_id integer null,
  team_city text null,
  team_name text null,
  team_abbreviation text null,
  organization text null,
  organization_type text null,
  player_profile_flag boolean null,
  constraint draft_history_pkey primary key (person_id, season, overall_pick)
);
create index if not exists idx_draft_history_overall_pick on public.draft_history using btree (overall_pick);
create index if not exists idx_draft_history_season on public.draft_history using btree (season);
create index if not exists idx_draft_history_team_id on public.draft_history using btree (team_id);

create table public.eligible_puzzles (
  id serial not null,
  puzzle_players jsonb not null,
  daily_theme text not null,
  created_at timestamp with time zone null default CURRENT_TIMESTAMP,
  updated_at timestamp with time zone null default CURRENT_TIMESTAMP,
  is_verified boolean null default false,
  add_to_puzzles boolean null default false,
  constraint eligible_puzzles_pkey primary key (id)
);
create index if not exists puzzle_players_gin_idx on public.eligible_puzzles using gin (puzzle_players);

create table public.franchise_leaders (
  id uuid not null default extensions.uuid_generate_v4(),
  team_id integer not null,
  team_name text not null,
  pts integer null,
  pts_person_id integer null,
  pts_player text null,
  ast integer null,
  ast_person_id integer null,
  ast_player text null,
  reb integer null,
  reb_person_id integer null,
  reb_player text null,
  blk integer null,
  blk_person_id integer null,
  blk_player text null,
  stl integer null,
  stl_person_id integer null,
  stl_player text null,
  created_at timestamp with time zone null default now(),
  updated_at timestamp with time zone null default now(),
  constraint franchise_leaders_pkey primary key (id),
  constraint unique_team_id unique (team_id)
);
create index if not exists idx_franchise_leaders_team_id on public.franchise_leaders using btree (team_id);

create table public.league_leaders (
  id serial not null,
  player_id integer null,
  rank integer null,
  player character varying(255) null,
  team character varying(50) null,
  gp integer null,
  min numeric(5,1) null,
  fgm numeric(5,1) null,
  fga numeric(5,1) null,
  fg_pct numeric(4,3) null,
  fg3m numeric(5,1) null,
  fg3a numeric(5,1) null,
  fg3_pct numeric(4,3) null,
  ftm numeric(5,1) null,
  fta numeric(5,1) null,
  ft_pct numeric(4,3) null,
  oreb numeric(5,1) null,
  dreb numeric(5,1) null,
  reb numeric(5,1) null,
  ast numeric(5,1) null,
  stl numeric(5,1) null,
  blk numeric(5,1) null,
  tov numeric(5,1) null,
  pf numeric(5,1) null,
  pts numeric(5,1) null,
  eff numeric(5,1) null,
  ast_tov numeric(5,2) null,
  stl_tov numeric(5,2) null,
  season character varying(7) null,
  stat_category character varying(10) null,
  constraint league_leaders_pkey primary key (id)
);
create index if not exists idx_player_id on public.league_leaders using btree (player_id);
create index if not exists idx_season_stat_category on public.league_leaders using btree (season, stat_category);

create table public.new_themes (
  theme_id bigint generated by default as identity not null,
  theme text not null,
  theme_description text not null,
  sql_query text not null,
  used_in_puzzle boolean null default false,
  constraint new_themes_pkey primary key (theme_id)
);
create index if not exists new_themes_used_puzzle_idx on public.new_themes using btree (used_in_puzzle);

create table public.player_awards (
  id serial not null,
  person_id integer not null,
  first_name character varying(50) null,
  last_name character varying(50) null,
  team character varying(50) null,
  description text null,
  all_nba_team_number integer null,
  season character varying(7) null,
  month integer null,
  week integer null,
  conference character varying(10) null,
  award_type character varying(50) null,
  subtype1 character varying(50) null,
  subtype2 character varying(50) null,
  subtype3 character varying(50) null,
  created_at timestamp with time zone null default CURRENT_TIMESTAMP,
  updated_at timestamp with time zone null default CURRENT_TIMESTAMP,
  constraint player_awards_pkey primary key (id)
);
create index if not exists idx_player_awards_person_id on public.player_awards using btree (person_id);
create index if not exists idx_player_awards_season on public.player_awards using btree (season);

create table public.player_career_stats (
  player_id integer not null,
  league_id character varying null,
  gp integer null,
  gs integer null,
  min double precision null,
  fgm integer null,
  fga integer null,
  fg_pct double precision null,
  fg3m integer null,
  fg3a integer null,
  fg3_pct double precision null,
  ftm integer null,
  fta integer null,
  ft_pct double precision null,
  oreb integer null,
  dreb integer null,
  reb integer null,
  ast integer null,
  stl integer null,
  blk integer null,
  tov integer null,
  pf integer null,
  pts integer null,
  constraint player_career_stats_pkey primary key (player_id)
);

create table public.puzzles (
  id bigint generated by default as identity not null,
  puzzle_id integer not null,
  date date not null,
  groups jsonb not null,
  author text not null,
  todays_theme text null,
  constraint puzzles_pkey primary key (id),
  constraint puzzles_date_key unique (date)
);

create table public.season_totals_regular_season (
  player_id integer not null,
  season_id character varying(7) not null,
  league_id character varying(3) null,
  team_id integer null,
  team_abbreviation character varying(3) null,
  player_age integer null,
  gp integer null,
  gs integer null,
  min numeric null,
  fgm integer null,
  fga integer null,
  fg_pct numeric null,
  fg3m integer null,
  fg3a integer null,
  fg3_pct numeric null,
  ftm integer null,
  fta integer null,
  ft_pct numeric null,
  oreb integer null,
  dreb integer null,
  reb integer null,
  ast integer null,
  stl integer null,
  blk integer null,
  tov integer null,
  pf integer null,
  pts integer null,
  constraint season_totals_regular_season_pkey primary key (player_id, season_id)
);

create table public.team_championships (
  id serial not null,
  team_id integer not null,
  team_name text not null,
  year_awarded integer not null,
  opposite_team text null,
  created_at timestamp with time zone null default CURRENT_TIMESTAMP,
  updated_at timestamp with time zone null default CURRENT_TIMESTAMP,
  constraint team_championships_pkey primary key (id),
  constraint team_championships_team_id_year_awarded_key unique (team_id, year_awarded)
);
create index if not exists idx_team_championships_team_id on public.team_championships(team_id);
create index if not exists idx_team_championships_year_awarded on public.team_championships(year_awarded);
create trigger update_team_championships_modtime before update on team_championships for each row execute function update_modified_column();

create table public.theme_players (
  theme_id integer not null,
  player_name text not null,
  player_id integer null,
  used_in_puzzle boolean null,
  constraint theme_players_pkey primary key (theme_id, player_name),
  constraint theme_players_theme_id_fkey foreign key (theme_id) references new_themes(theme_id)
);

create table public.themes (
  theme_id bigint generated by default as identity not null,
  theme text not null,
  color text not null,
  emoji text not null,
  words jsonb not null,
  used_in_puzzle boolean null default false,
  validated_state boolean null default false,
  constraint themes_pkey primary key (theme_id)
);
create index if not exists themes_color_idx on public.themes(color);
create index if not exists themes_used_puzzle_idx on public.themes(used_in_puzzle);

-- ===== end of DDL snapshot =====
```

---

## 12. Next Steps

* Decide whether to export *all* tables or only the few required by the game (likely `puzzles`, `themes`, `theme_players`).
* Build an Apps Script that emulates the `select ... eq('date', ...)` query on the *Puzzles* sheet.
* Replace `createClient()` with a lightweight fetch to Google Sheets API / public JSON feed.

---

## 13. Reference DDL (current Postgres structures)

> The full CREATE TABLE / INDEX statements below are a verbatim snapshot of the production database on **2025‑06‑26**. Keep them with the repo so you can recreate the schema anywhere (e.g.
>  `psql -f schema.sql`).
>
> <details>
> <summary>Click to expand SQL (very large)</summary>
>
> ```sql
> -- ——— core stats ———
> create table public.all_time_leaders (
>   id bigint generated by default as identity not null,
>   player_id integer not null,
>   player_name text not null,
>   stat_value numeric not null,
>   stat_rank integer not null,
>   stat_category text not null,
>   constraint all_time_leaders_pkey primary key (id),
>   constraint all_time_leaders_player_id_stat_category_key unique (player_id, stat_category)
> );
> create index if not exists idx_all_time_leaders_player_id on public.all_time_leaders(player_id);
> create index if not exists idx_all_time_leaders_stat_category on public.all_time_leaders(stat_category);
>
> create table public.common_player_info (
>   player_id integer primary key,
>   first_name varchar,
>   last_name varchar,
>   display_first_last varchar,
>   display_last_comma_first varchar,
>   display_fi_last varchar,
>   player_slug varchar,
>   birthdate date,
>   school varchar,
>   country varchar,
>   last_affiliation varchar,
>   height varchar,
>   weight integer,
>   season_exp integer,
>   jersey varchar,
>   position varchar,
>   roster_status boolean,
>   team_id integer,
>   team_name varchar,
>   team_abbreviation varchar,
>   team_code varchar,
>   team_city varchar,
>   playercode varchar,
>   from_year integer,
>   to_year integer,
>   dleague_flag boolean,
>   nba_flag boolean,
>   games_played_flag boolean,
>   draft_year integer,
>   draft_round integer,
>   draft_number integer
> );
>
> create table public.common_team_roster (
>   team_id integer not null,
>   team_name text,
>   season text not null,
>   leagueid text,
>   player text,
>   player_slug text,
>   num text,
>   position text,
>   height text,
>   weight text,
>   birth_date text,
>   age integer,
>   exp text,
>   school text,
>   player_id integer not null,
>   how_acquired text,
>   nickname text,
>   constraint common_team_roster_pkey primary key (team_id, player_id, season)
> );
> create index if not exists idx_common_team_roster_player_id on public.common_team_roster(player_id);
> create index if not exists idx_common_team_roster_season on public.common_team_roster(season);
> create index if not exists idx_common_team_roster_team_id on public.common_team_roster(team_id);
>
> create table public.common_team_roster_coaches (
>   team_id integer not null,
>   team_name text,
>   season text not null,
>   coach_id integer not null,
>   first_name text,
>   last_name text,
>   coach_name text,
>   is_assistant boolean,
>   coach_type text,
>   sort_sequence integer,
>   constraint common_team_roster_coaches_pkey primary key (team_id, coach_id, season)
> );
> create index if not exists idx_common_team_roster_coaches_coach_id on public.common_team_roster_coaches(coach_id);
> create index if not exists idx_common_team_roster_coaches_season on public.common_team_roster_coaches(season);
> create index if not exists idx_common_team_roster_coaches_team_id on public.common_team_roster_coaches(team_id);
>
> create table public.draft_history (
>   person_id integer not null,
>   player_name text,
>   season integer not null,
>   round_number integer,
>   round_pick integer,
>   overall_pick integer not null,
>   draft_type text,
>   team_id integer,
>   team_city text,
>   team_name text,
>   team_abbreviation text,
>   organization text,
>   organization_type text,
>   player_profile_flag boolean,
>   constraint draft_history_pkey primary key (person_id, season, overall_pick)
> );
> create index if not exists idx_draft_history_overall_pick on public.draft_history(overall_pick);
> create index if not exists idx_draft_history_season on public.draft_history(season);
> create index if not exists idx_draft_history_team_id on public.draft_history(team_id);
>
> -- (remaining tables omitted here for brevity – they are identical to the block provided by the user)
> ```
>
> </details>
>
> *Tip: keep this section collapsed in the rendered docs to avoid noise.*

### Changelog

* **2025‑06‑26** – Initial documentation extracted from repository tree.

---

Happy hoop‑hacking! 🏀
