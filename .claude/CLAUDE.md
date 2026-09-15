# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

LFL is a Streamlit dashboard that analyzes team performance in a Sleeper fantasy football league. It pulls live data from the public Sleeper API (no auth required), computes standings/seeding/expected-wins metrics, and renders them across several tabs.

## Commands

```bash
# Activate the existing venv (already populated at ./env)
source env/bin/activate

# Install/sync dependencies
pip install -r requirements.txt

# Run the app (must be run from the repo root — app.py appends ./src/Classes
# and ./src/Pages to sys.path using relative paths)
streamlit run src/app.py
```

There are no automated tests, linter, or build step configured in this repo.

## Architecture

### Data flow

`league_config.json` (league_id, division→team mappings) is the only local config. On startup, `FantasyLeague(from_json=...)` (`src/Classes/FantasyLeague.py`) hits three Sleeper endpoints — league users, rosters, and per-week matchups — and builds an in-memory model:

1. `retrieve_teams`: joins Sleeper users + rosters into `Team` objects keyed by `roster_id`; team `division` comes from `league_config.json`, not the API (see TODO comment in code).
2. `retrieve_scoring`: for every completed week, pulls matchups, ranks teams by points within the week, pairs each team with its matchup opponent, and inserts a `WeekPerformance` into the corresponding `Team`.
3. `update_seeding`: runs the `SeedEngine` (division seeding, then league seeding) over all teams.

`FantasyLeague` exposes the computed state only as pandas DataFrames (`getTeamsDf`, `getScoringDf`, `getH2hDf`) — Streamlit pages never touch `Team`/`WeekPerformance` objects directly.

`src/app.py` wraps league construction in `@st.cache_resource` (`init_league`), so the Sleeper API is only called once per server process; restart Streamlit to pick up new game results. The three DataFrames are stashed in `st.session_state` and each page module receives the DataFrames it needs as plain function arguments — there's no shared page-level state beyond that.

### Class responsibilities (`src/Classes/`)

- **Team.py** — `Team` (per-roster identity, record, division record, H2H lookups) and `WeekPerformance` (single-week result incl. opponent data and win/loss). Each `Team` owns a `MetricsManager` that recomputes derived metrics every time a week is inserted.
- **Metrics.py** — small `Metric` subclasses (`AverageMetric`, `MedianMetric`, `StdDevMetric`, `ExpectedWinsMetric`, `ProbNWins`). `MetricsManager.update` is the single place that defines which metrics exist and how they're keyed (`avg`, `std`, `med`, `last5`, `CEW` = campaign expected wins from own weekly rank, `SEW` = strength-of-schedule expected wins from opponents' weekly rank, `probNWins` = full win-count probability distribution via brute-force combinatorics over per-week win probabilities). Column names in this dict are the same keys used later in the DataFrames and Streamlit pages, so renaming a metric key means updating every page that reads it.
- **SeedEngine.py** — a criteria-chain seeding system: `SeedCriteria` subclasses each implement one pairwise comparison rule (record, H2H, division record, expected wins, division seed, etc.) returning 1/-1/0; a `Seeder` walks its `criteria_chain` in order via `cmp_to_key`, falling through to the next criterion on a tie. `DivisionSeeder`/`LeagueSeeder` are generic base classes; `LFLDivisionSeeder`/`LFLLeagueSeeder` fix the LFL-specific tiebreaker order and are the ones actually wired up in `FantasyLeague.__init__`. League seeding depends on `division_seed` already being set, so `SeedEngine.calculate_and_update_seeding` always runs division seeding before league seeding. To change tiebreaker rules, edit the `criteria_chain` list on the relevant `LFL*Seeder`; to add a new rule, add a `SeedCriteria` subclass and insert it into the chain.
- **Charts.py** — matplotlib-based chart classes (`LeagueBoxPlot`, `LeaguePerformanceChart`, `LeagueExpWChart`, `LeagueProbChart`) that write to `./output/`. These predate the Altair-based charts now used in `src/Pages/` and are not called from `app.py`/`Pages`; `FantasyLeague.ipynb` is the older notebook-based version of this analysis and exercises these classes directly.

### Pages (`src/Pages/`)

Each file exposes one `render_*(teams_df, ...)` function called from `src/app.py` inside an `st.tabs` block; pages take DataFrames in and call `st.*` directly (no return value). Charting in pages uses `st.line_chart`/`altair` rather than `Charts.py`. UI text is in Portuguese (pt-BR); keep new UI strings consistent with that.

### Notebook

`FantasyLeague.ipynb` is a standalone, older exploratory version of this same analysis (predates the `src/` package split) — not imported by the app. Treat it as historical/reference, not a dependency of the Streamlit app.
