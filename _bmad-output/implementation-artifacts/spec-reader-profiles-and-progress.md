---
title: 'Reader Profiles & Reading Progress Tracking (FR-7, FR-8: Readers, Reading Sessions, Milestones, Page progress)'
type: 'feature'
created: '2026-08-20'
status: 'done'
baseline_commit: 'ed6a1e0bf7e2ec8328b39a2e992ce8605e6fa65a'
review_loop_iteration: 1
context:
  - '_bmad-output/planning-artifacts/architecture/architecture-pothi-parivaar-2026-08-20/ARCHITECTURE-SPINE.md'
  - '_bmad-output/planning-artifacts/prds/prd-pothi-parivaar-2026-08-20/prd.md'
  - 'AGENTS.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Family members currently have only basic placeholder reader actions with browser prompts, lacking comprehensive reader profile customization (age group, roles), active reading session summaries, interactive page progress dialogs, completion history logs, and dedicated reader statistics.

**Approach:** Implement full reader profile lifecycle management (CRUD with age group/role and avatars), an aggregated family reading activity endpoint (`GET /api/v1/readers/activity`), reader reading statistics and history, smooth interactive Vuetify 3 dialogs for updating page progress and finishing books with celebrations, and seamless "Start Reading" integration across the book catalog and reader views.

## Boundaries & Constraints

**Always:**
- Use FastAPI + Pydantic v2 schemas and SQLite in WAL mode (`data/pothi.db`).
- Use Vuetify 3 Material Design 3 components without custom CSS or theme bloat.
- When a reading session is marked as `finished`, automatically record the `finish_date` and increment the parent book's `read_count`.
- Maintain single-tenant frictionless family UX with zero password/login walls.
- Follow Git branching policy on `feat/reader-profiles-tracking`.

**Ask First:**
- Introducing gamification or external reward integrations outside the family reading tracker scope.
- Enforcing mandatory reader assignments for book browsing.

**Never:**
- Authentication / password gating for selecting family reader profiles.
- Modifying or breaking existing book catalog and ISBN lookup routes.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| List Active Activity | `GET /api/v1/readers/activity` | 200 OK with list of active sessions containing nested reader and book metadata | Returns `[]` if no active sessions exist |
| Create Reader | `POST /api/v1/readers` with name, avatar, age_group | 201 Created with new reader record | 400 Bad Request if reader name already exists |
| Update Reader | `PUT /api/v1/readers/{id}` with updated fields | 200 OK with updated reader | 404 Not Found if reader does not exist |
| Delete Reader | `DELETE /api/v1/readers/{id}` | 204 No Content; cascades or cleans up reader sessions | 404 Not Found if reader does not exist |
| Start Reading Book | `POST /api/v1/readers/sessions` with book_id, reader_id, start_page | 201 Created with active session | 404 Not Found if book or reader does not exist |
| Update Page Progress | `PUT /api/v1/readers/sessions/{id}` with `current_page: 85` | 200 OK with updated page; progress % calculated | 400 if current_page > book page_count (capped/warned) |
| Complete Book | `PUT /api/v1/readers/sessions/{id}` with `status: "finished"` | 200 OK; sets finish_date to today, increments book `read_count` | 404 Not Found if session does not exist |
| Get Reader Stats | `GET /api/v1/readers/{id}/stats` | 200 OK with `total_finished`, `total_reading`, `total_pages_read`, `history` | 404 Not Found if reader does not exist |

</frozen-after-approval>

## Code Map

- `app/models.py` -- SQLModel entities `Reader`, `ReadingSession`, and Pydantic schemas (`ReaderUpdate`, `ReaderActivityRead`, `ReaderStatsRead`)
- `app/api/readers.py` -- Endpoints for reader CRUD, reader activity aggregation (`/activity`), reader stats (`/{id}/stats`), and session management
- `frontend/src/services/api.js` -- API client methods for reader updates, deletes, activity fetch, stats, and session operations
- `frontend/src/components/ReaderTracker.vue` -- Rich Vuetify 3 component for family reader profiles, active reading cards, progress bars, page update modal, and finish celebration
- `frontend/src/components/BookDetailDialog.vue` -- Integrates "Start Reading" reader selector directly into book detail view
- `frontend/src/components/BookCard.vue` -- Shows active reading badges on catalog cards
- `frontend/src/App.vue` -- Navigation coordinator with active reader filter and view switcher
- `tests/test_readers_and_sessions.py` -- Pytest suite validating reader CRUD, session progress, stats, and book completion increments

## Tasks & Acceptance

**Execution:**
- [x] `app/models.py` -- Add `age_group` to `Reader`, update session schemas and add `ReaderActivityRead`, `ReaderStatsRead` DTOs -- Supports rich reader data & single-query activity responses
- [x] `app/api/readers.py` -- Implement reader update/delete endpoints, `/activity` aggregated endpoint, reader `/stats`, and robust session lifecycle transitions -- Provides comprehensive REST API
- [x] `frontend/src/services/api.js` -- Add frontend API client methods for all reader and session operations -- Connects frontend with new backend endpoints
- [x] `frontend/src/components/ReaderTracker.vue` -- Build enhanced UI with reader profile chips, active reading cards, Vuetify dialogs for page updates & finish celebration, and reader history tab -- Delivers delightful, accessible family reading experience
- [x] `frontend/src/components/BookDetailDialog.vue` & `frontend/src/components/BookCard.vue` -- Add quick reader assignment and active reader status indicators to books -- Connects catalog with reading tracker
- [x] `frontend/src/App.vue` -- Update layout with quick reader switcher and streamlined tab/view coordination -- Seamless navigation across catalog and reading tracker
- [x] `tests/test_readers_and_sessions.py` -- Write comprehensive automated tests for all reader & session flows -- Guarantees stability and correctness

**Acceptance Criteria:**
- Given an existing book and reader, when a reading session is created and updated to `status: finished`, then the book's `read_count` increments by 1 and the completion is visible in reader stats.
- Given active reading sessions across multiple family members, when `GET /api/v1/readers/activity` is called, then all active reading sessions return with populated reader and book details in one response.
- Given the web frontend, when a family member updates their current page or finishes a book, the UI updates smoothly without browser `prompt`/`confirm` alerts and shows celebratory feedback.
- Given `pytest tests/`, all backend tests pass cleanly.

## Spec Change Log

## Design Notes

- **Aggregated Activity API**: Rather than triggering N+1 roundtrips from the browser to resolve reader and book metadata for each active session, `GET /api/v1/readers/activity` joins `ReadingSession`, `Reader`, and `Book` to provide a single-shot payload.
- **Completion Invariant**: When status transitions to `finished`, `finish_date` defaults to today (`date.today()`) if not supplied, and `book.read_count += 1` is committed in the same database transaction.
- **Child-Friendly Progress Dialog**: Instead of disruptive native alerts, page updates use a `v-dialog` featuring both a slider and numeric stepper for easy touch control on mobile and tablet screens.

## Verification

**Commands:**
- `pytest tests/test_readers_and_sessions.py tests/test_api.py` -- expected: All backend tests pass
- `cd frontend && npm run build` -- expected: Production bundle builds cleanly without errors

## Suggested Review Order

**Reading lifecycle API**

- Enforces progress, completion, and read-count invariants in one transaction.
  [`readers.py:237`](../../app/api/readers.py#L237)

- Returns joined reader and book activity without browser-side request fan-out.
  [`readers.py:49`](../../app/api/readers.py#L49)

**Schema compatibility**

- Adds profile and session fields safely for existing SQLite family libraries.
  [`database.py:25`](../../app/database.py#L25)

- Defines typed reader, session, activity, and statistics API contracts.
  [`models.py:29`](../../app/models.py#L29)

**Family reading experience**

- Provides profile management, page updates, finishing, and history in Vuetify dialogs.
  [`ReaderTracker.vue:1`](../../frontend/src/components/ReaderTracker.vue#L1)

- Starts sessions directly from book details and displays shared reading history.
  [`BookDetailDialog.vue:1`](../../frontend/src/components/BookDetailDialog.vue#L1)

- Coordinates catalog reading badges and responsive tracker navigation.
  [`App.vue:138`](../../frontend/src/App.vue#L138)

**Verification**

- Covers CRUD, lifecycle, activity, statistics, validation, and schema upgrades.
  [`test_readers_and_sessions.py:1`](../../tests/test_readers_and_sessions.py#L1)

### Review Findings

- [x] [Review][Decision] Catalog-level reader switcher in App.vue — dismissed: keep switcher in the tracker only
- [x] [Review][Decision] Finish rating default 5 vs optional — dismissed: keep default 5

- [x] [Review][Patch] Cap current_page to book page_count and warn in the page dialog [`app/api/readers.py:258`]
- [x] [Review][Patch] Reject or reuse duplicate active sessions for the same reader+book [`app/api/readers.py:268`]
- [x] [Review][Patch] Catalog fetch should not blank the library when activity fails [`frontend/src/App.vue:304`]
- [x] [Review][Patch] Cascade or clean up reading sessions when deleting a book [`app/services/book_service.py:63`]
- [x] [Review][Patch] Decrement book `read_count` when deleting a reader who has finished sessions [`app/api/readers.py:125`]
- [x] [Review][Patch] Surface reader/session API errors in the UI instead of `console.error` only [`frontend/src/components/ReaderTracker.vue:744`]
- [x] [Review][Patch] Finish date should use local calendar date, not UTC ISO [`frontend/src/components/ReaderTracker.vue:822`]
- [x] [Review][Patch] Replace remaining `window.confirm` calls with Vuetify dialogs [`frontend/src/components/ReaderTracker.vue:768`]
- [x] [Review][Patch] Trim reader names and reject blank/whitespace names [`app/api/readers.py:36`]
- [x] [Review][Patch] Book-detail load should not drop readers when sessions fail [`frontend/src/components/BookDetailDialog.vue:164`]
- [x] [Review][Patch] Do not show stale stats when a different reader’s stats request fails [`frontend/src/components/ReaderTracker.vue:708`]
- [x] [Review][Patch] Clear `finish_date` when moving a session off `finished` [`app/api/readers.py:329`]
- [x] [Review][Patch] Start-reading book picker is silently capped at 300 titles [`frontend/src/components/ReaderTracker.vue:854`]
- [x] [Review][Patch] Backfill `created_at` when adding the column to existing reader rows [`app/database.py:38`]
- [x] [Review][Patch] Close verification gaps: session DELETE, activity after finish, notes persistence, create-time page cap, update-time duplicate name, migration preserves existing rows [`tests/test_readers_and_sessions.py:1`]

- [x] [Review][Defer] Catalog `GET /books` default `limit=100` [`app/api/books.py:26`] — deferred, pre-existing
