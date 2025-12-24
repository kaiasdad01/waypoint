# Status Guide Codebase Review

Focus: simplification, ease of update/reading, and scalability. File references point to the current codebase locations that motivate each change.

## Repository hygiene and structure
- Remove committed virtualenv and cache artifacts to reduce repo size and noise; currently `venv/`, `src/status_optimizer/__pycache__/`, `tests/__pycache__/`, and `src/status_guide.egg-info/` are present despite `.gitignore` covering them.
- Remove temporary Excel lock files like `data/~$united-routes.xlsx` and treat `data/united-routes.xlsx` as external sample data (download or generate in a setup step) to keep the repo lean.
- Add a clear `docs/` index and move long-form research into `docs/` or drop it if not used by the optimizer workflow; the current `United-Airlines-Research.md` is not referenced anywhere.
- Add a small `Makefile` or `justfile` with common commands (setup, test, run) to reduce README churn; currently commands are repeated manually in `README.md`.

## Documentation and onboarding
- Replace the “Phase 0/1/2” roadmap in `README.md` with a short “Current capabilities + next 3 prioritized items” list so updates are easier and less speculative.
- Update CLI examples in `README.md` to show the installed entrypoint (`status-optimizer ...`) instead of `python -m ...`, which drifts from `project.scripts` in `pyproject.toml`.
- Add a brief “data expectations” section describing required Excel columns and formats to reduce tribal knowledge currently buried in `src/status_optimizer/data/providers/excel_flight_feed.py`.

## Domain model simplification
- Convert `Flight` and `Segment` to `@dataclass(frozen=True)` and drop manual `__eq__`, `__hash__`, and verbose docstrings; validation can move to `__post_init__` for clarity (`src/status_optimizer/domain/flight.py`, `src/status_optimizer/domain/segment.py`).
- Make `Itinerary` a thin data object with computed properties and move validation logic to a factory or validator function to keep construction lightweight (`src/status_optimizer/domain/itinerary.py`).
- Standardize type hints to modern `list[...]`/`dict[...]` and remove unused imports like `Optional` in `src/status_optimizer/domain/segment.py`.

## Search scalability
- Pre-sort outbound and inbound flights once in `FlightGraph` and use binary search (bisect) for time filtering to avoid sorting on every query (`src/status_optimizer/search/graph.py`).
- Add a visited-state cache keyed by `(airport, legs_used, time_bucket)` or similar to reduce duplicate exploration in `BeamSearch` (`src/status_optimizer/search/beam_search.py`).
- Make `beam_width`, `max_candidates`, and scaling rules configurable via CLI or config file instead of hard-coded heuristics (`src/status_optimizer/search/search.py`, `src/status_optimizer/cli/main.py`).
- Enforce `time_window_end` in graph queries or remove the parameter to avoid misleading logic; it is passed through but never used for pruning or filtering (`src/status_optimizer/search/beam_search.py`, `src/status_optimizer/search/search.py`).
- Split `ItinerarySearch.search` into smaller steps (load flights, build graph, run search, post-process) for readability and easier extension (`src/status_optimizer/search/search.py`).

## Data ingestion and normalization
- Replace the stubbed `local_time_to_utc_datetime` with a real timezone-aware conversion (zoneinfo or airport timezone map) and keep the Phase 0 simplification in a separate adapter to avoid silent inaccuracies (`src/status_optimizer/data/providers/normalizers.py`).
- Cache generated flights by date range and DOW to avoid repeatedly expanding the same Excel rows for repeated searches (`src/status_optimizer/data/providers/excel_flight_feed.py`).
- Store column mappings in a small config dataclass and allow overrides in the CLI to make data format updates safer (`src/status_optimizer/data/providers/excel_flight_feed.py`).
- Validate required columns once at load time and emit a single structured error; right now missing columns cause repeated per-row failures and unclear logs.

## CLI and UX
- Replace `print`-based errors with logging + consistent error codes, and centralize error formatting in one place (`src/status_optimizer/cli/main.py`).
- Remove unused parameters from `build_constraints` or actually add `TimeWindowConstraint` there; currently `start_time` and `end_time` are passed but ignored (`src/status_optimizer/cli/main.py`).
- Move defaults into constants (e.g., `DEFAULT_MIN_LAYOVER_MINUTES`) to keep README, CLI help, and tests aligned (`src/status_optimizer/cli/main.py`, `README.md`).

## Tests and maintainability
- Reduce boilerplate docstrings in tests to improve signal-to-noise; the current test files are verbose for simple assertions (`tests/unit/test_search.py`, `tests/unit/test_flight.py`).
- Add a small set of high-value integration tests for timezones and DOW parsing instead of many synthetic search tests; these are the most brittle pieces of logic (`src/status_optimizer/data/providers/normalizers.py`).

## AI-written code flags
These look strongly AI-generated due to verbose template docstrings, repeated explanatory comments, and speculative TODOs. Consider rewriting by hand or trimming for clarity.
- Overly structured, repetitive docstrings across domain and search modules, often restating the code line-by-line (`src/status_optimizer/domain/flight.py`, `src/status_optimizer/domain/itinerary.py`, `src/status_optimizer/search/beam_search.py`).
- Long, generic, citation-free “research report” content that is not tied to any code use and reads like a generic summary (`United-Airlines-Research.md`).
- Multiple “Phase 0” narrative comments and TODOs that do not map to a tracked plan or issues, typical of LLM scaffolding (`src/status_optimizer/data/providers/normalizers.py`, `README.md`).

## Suggested file-level refactors (prioritized)
- Simplify models with dataclasses and move validation to a dedicated validator (`src/status_optimizer/domain/flight.py`, `src/status_optimizer/domain/segment.py`, `src/status_optimizer/domain/itinerary.py`).
- Pre-index flights in `FlightGraph` and add bisect-based time filtering (`src/status_optimizer/search/graph.py`).
- Make search parameters configurable and remove hard-coded scaling rules (`src/status_optimizer/search/search.py`, `src/status_optimizer/cli/main.py`).
- Replace stub timezone conversion with real `zoneinfo` logic and add a minimal airport->timezone mapping config (`src/status_optimizer/data/providers/normalizers.py`).
- Remove committed build artifacts and venv, and add a short data setup script (`venv/`, `src/status_guide.egg-info/`, `data/united-routes.xlsx`).
