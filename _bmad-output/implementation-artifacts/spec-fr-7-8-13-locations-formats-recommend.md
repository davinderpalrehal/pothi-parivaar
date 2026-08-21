---
title: 'Hierarchical Physical Location Management (FR-7)'
type: 'feature'
created: '2026-08-20'
status: 'done'
baseline_commit: '9afd10118d372c6672daf03115bef8dcddafd59f'
review_loop_iteration: 1
context:
  - '_bmad-output/planning-artifacts/architecture/architecture-pothi-parivaar-2026-08-20/ARCHITECTURE-SPINE.md'
  - '_bmad-output/planning-artifacts/prds/prd-pothi-parivaar-2026-08-20/prd.md'
  - 'AGENTS.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Add/edit book forms use three free-text location fields, so the same shelf is typed inconsistently and families cannot pick an existing Room → Unit → Shelf. The Location table and `POST /locations` exist but books never write to them; ShelfManager only browses book occupancy.

**Approach:** Keep `Book.location_room` / `location_unit` / `location_shelf` as the source of truth (AD-5). Use `Location` as a 3-tier autocomplete registry: pick an existing triple or type a new one, upserting on save. ShelfManager can add a shelf; the map includes registered shelves with zero books.

## Boundaries & Constraints

**Always:**
- FastAPI + Pydantic v2, SQLite WAL (`data/pothi.db`), `/api/v1/`, Vue 3 + Vuetify 3 only. Branch `feat/hierarchical-locations`.
- No `location_id` FK. Display string is `room / unit / shelf`.
- `POST /books` never calls ISBN lookup. Catalog AND filters (`room` exact match) stay as they are.
- Location upsert is case-insensitive on the stripped triple; blank unit/shelf stored as `""` not null.

**Ask First:**
- Replacing denormalized location fields with a `location_id` FK.
- Location delete/rename that rewrites existing books.

**Never:**
- FR-8 digital_link / format icons; FR-13 recommend endpoint; auth; custom CSS.
- Changing `app/api/readers.py`, `ReaderTracker.vue`, or ISBN isolation.
- Browser `prompt` / `confirm` / `alert`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Pick existing | Combobox options from `GET /locations`; save book | Book `location_*` set; registry unchanged | Empty location allowed (no upsert) |
| Type new on book save | New room/unit/shelf on add or edit | Book saved; Location upserted once | Repeat triple does not duplicate |
| Direct registry create | `POST /locations` same triple twice | Second call returns the existing row (not a second id) | 422 if `room` blank |
| Summary map | `GET /locations/summary` | Rooms/units/shelves from registry ∪ book occupancy; `book_count` from Book rows | Unassigned bucket only for books with null room |
| ShelfManager add | Create shelf on the map view | Registry row exists; chip shows with `book_count` 0 until a book uses it | `filter-room` emit unchanged |

</frozen-after-approval>

## Code Map

- `app/models.py` -- `Book.location_*` L21–23 (source of truth). `Location` L48–53 has no unique triple. `LocationCreate`/`LocationRead` L182–192.
- `app/api/locations.py` -- `GET ""` L9–12; `POST ""` L15–25 always inserts; `GET /summary` L28–52 reads **Book only**, so empty registry shelves are invisible.
- `app/services/book_service.py` -- `create_book` L6–12 ISBN-isolated; `update_book` L80–88; room filter L55–56. Upsert Location after create/update when room is non-blank. Do not change filter joins.
- `app/database.py` -- `migrate_schema` L25–51. Unique index MUST be on `lower(trim(room)), lower(trim(unit)), lower(trim(shelf))` — not raw columns. Also backfill distinct non-blank `Book.location_*` triples into `Location` before creating the index.
- `frontend/src/services/api.js` -- `getLocations` L73–74 unused; `getLocationsSummary` L76–77 used. Add `createLocation`.
- `frontend/src/components/AddBookDialog.vue` -- free-text L134–156 → `v-combobox` from `getLocations`.
- `frontend/src/components/BookDetailDialog.vue` -- edit L59–81; view ` / ` join L143–144. Same comboboxes.
- `frontend/src/components/ShelfManager.vue` -- browse L18–47; `filter-room` L40; `loadLocations` L61–77. Add create-shelf; keep emit.
- `frontend/src/App.vue` -- `handleFilterRoom` L420–424; refresh shelves on save L398, L413.
- Read-only: `app/api/isbn.py`, `app/api/readers.py`, `BookCard.vue` location chip L26–34 / L102–104.
- Tests: `tests/test_catalog_and_isbn.py` room filter + location PUT. New `tests/test_locations.py`.

## Tasks & Acceptance

**Execution:**
- [x] `app/models.py` + `app/database.py` + `app/api/locations.py` -- Case-insensitive unique triple (`lower(trim(...))`); idempotent POST upsert (201 insert / 200 same id); summary unions registry with Book counts; occupancy Unassigned must not merge with a registry room named Unassigned -- FR-7 registry API
- [x] `app/services/book_service.py` -- Strip then upsert Location on create/update when room is non-blank; do not rewrite other book fields; leave ISBN isolation and exact `room` filter untouched -- Books populate the picker
- [x] `frontend/src/services/api.js` + `AddBookDialog.vue` + `BookDetailDialog.vue` + `ShelfManager.vue` -- Combobox picker (case-insensitive cascade; empty unit/shelf stay selectable); load options when dialog opens including already-open; `createLocation`; ShelfManager add-shelf; keep `filter-room` -- FR-7 UI
- [x] `tests/test_locations.py` -- Matrix plus: case-variant POST same id, migrate_schema on a legacy location table, mixed-case occupancy one summary chip, room-only shelf `unit`/`shelf` `""` with `book_count` 0 then 1 -- Locks edges

**Acceptance Criteria:**
- Given registered shelves, when add/edit picks one or types a new triple, then the book stores `location_*` and the registry contains that triple once.
- Given a shelf created on the map with no books, when summary loads, then the chip appears with `book_count` 0 and clicking it still filters the catalog by room.
- Given `pytest tests/`, existing catalog/reader/hermes tests and `tests/test_locations.py` all pass.

## Spec Change Log

- review_loop 1: Case-sensitive `UNIQUE(room,unit,shelf)` and case-sensitive combobox filters contradicted the frozen case-insensitive upsert key; Code Map told migrate to index raw columns, so derivation followed the wrong unique. Amended Code Map, tasks, and Design Notes to require `lower(trim(...))` uniqueness, strip in `find_location`, Book→Location backfill on migrate, case-insensitive combobox cascade that keeps empty unit/shelf, `immediate` option load, 200 when upsert returns an existing row, and tests for migrate / mixed-case summary / room-only shelves. Avoids duplicate `Office`/`office` registry rows and empty pickers on existing catalogs. KEEP: shared upsert/summary helper; 201 insert / 200 duplicate same `id`; summary unions registry with occupancy; `v-combobox` add/edit + ShelfManager Add Shelf; `filter-room` emit unchanged; no `location_id` FK; ISBN isolation; exact catalog `room` filter; blank unit/shelf stored as `""`; `LocationCreate` 422 on blank room.

## Design Notes

Registry is autocomplete, not a parent row. Upsert **and** DB unique key are `lower(trim(room))|lower(trim(unit))|lower(trim(shelf))`. `find_location` must strip and lower the incoming triple. Skip upsert when room is empty. Do not copy canonical casing onto `Book.location_*` (exact catalog `room` filter stays).

`migrate_schema` backfills distinct book triples with a non-blank room, coalesces NULL unit/shelf to `""`, then creates the expression unique index if missing.

Summary merges registry (`book_count` 0) with Book occupancy using the same normalized key. Occupancy Unassigned is books with null/blank room only — use a sentinel map key so a real room named `Unassigned` does not absorb those counts. Empty unit/shelf chips must still render a usable label (not `" / "`).

`POST /locations`: 201 on first insert; 200 with the same `id` when the triple already exists (including IntegrityError recovery). OpenAPI should advertise both.

Combobox room/unit/shelf filters compare case-insensitively after trim; `""` unit/shelf remain in the item list. Watch `modelValue` with `immediate: true` so an already-open add dialog still loads `GET /locations`.

## Verification

**Commands:**
- `pytest tests/test_locations.py tests/test_catalog_and_isbn.py tests/test_api.py tests/test_readers_and_sessions.py tests/test_hermes_skill.py -q` -- expected: all pass
- `python -c "from app.main import app"` -- expected: imports without error

## Suggested Review Order

**Case-insensitive registry**

- Upsert skips blank rooms and reuses the stripped, lowercased triple.
  [`location_service.py:60`](../../app/services/location_service.py#L60)

- POST returns 201 on insert and 200 with the same id on a duplicate.
  [`locations.py:25`](../../app/api/locations.py#L25)

- Blank room is 422; blank unit/shelf persist as empty strings.
  [`models.py:190`](../../app/models.py#L190)

**Existing catalogs**

- Backfill distinct book triples, then create the expression unique index.
  [`database.py:67`](../../app/database.py#L67)

**Book save without an FK**

- Strip location fields, then upsert only when room is non-blank.
  [`book_service.py:27`](../../app/services/book_service.py#L27)

- Occupancy Unassigned stays off a real room named Unassigned.
  [`location_service.py:93`](../../app/services/location_service.py#L93)

**Pick-or-type UI**

- Add-book comboboxes load GET /locations, including an already-open dialog.
  [`AddBookDialog.vue:135`](../../frontend/src/components/AddBookDialog.vue#L135)

- Edit uses the same cascade and reloads options after a successful save.
  [`BookDetailDialog.vue:60`](../../frontend/src/components/BookDetailDialog.vue#L60)

- Map Add Shelf registers a zero-count chip; filter-room emit is unchanged.
  [`ShelfManager.vue:14`](../../frontend/src/components/ShelfManager.vue#L14)

**Tests**

- Matrix plus migrate, mixed-case occupancy, and room-only shelves.
  [`test_locations.py:316`](../../tests/test_locations.py#L316)

