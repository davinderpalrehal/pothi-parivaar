---
title: 'Catalog CRUD, Search/Filters, and Dual Ingestion (FR-1–FR-6)'
type: 'feature'
created: '2026-08-20'
status: 'done'
baseline_commit: '66945f86e9341ab91ecc9b9ed80c3bf0c1ab2368'
review_loop_iteration: 0
context:
  - '_bmad-output/planning-artifacts/architecture/architecture-pothi-parivaar-2026-08-20/ARCHITECTURE-SPINE.md'
  - '_bmad-output/planning-artifacts/prds/prd-pothi-parivaar-2026-08-20/prd.md'
  - 'AGENTS.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The catalog scaffold creates, lists, and deletes books and looks up ISBNs, but families cannot edit a book, filter by format/location/reading status, or add a stack quickly. Delete uses browser `confirm`, add-book errors are silent, and there is no Save & Add Next — blocking UJ-1, UJ-2, and UJ-3.

**Approach:** Close those gaps on the existing FastAPI book/ISBN routes and Vue catalog: server-side multi-filters, edit from book detail, Vuetify delete confirmation, visible add-book errors, and Save & Add Next. ISBN lookup stays advisory prefill and never blocks manual `POST /books`.

## Boundaries & Constraints

**Always:**
- FastAPI + Pydantic v2, SQLite WAL (`data/pothi.db`), `/api/v1/` routes, Vue 3 + Vuetify 3 only (no new custom CSS/themes).
- `POST /api/v1/books` must never call `GET /api/v1/isbn/{isbn}`. Lookup is prefill; fields stay editable; ISBN 404 continues as manual entry (AD-4).
- Cover is `cover_url` only. Work on `feat/catalog-and-dual-ingestion`.
- Do not change `app/api/readers.py` or `ReaderTracker.vue`. A read-side session join inside `list_books` is allowed for the status filter. Keep `GET /api/v1/books/{id}/sessions` as detail history.

**Ask First:**
- A second ISBN provider (e.g. Google Books), soft-delete/archive, cover upload, or changing default `GET /books` `limit=100`.

**Never:**
- Location manager / ShelfManager rewrite (FR-7) or a format-registry UI (FR-8). Location stays `location_room` / `location_unit` / `location_shelf` on the book form.
- Auth, Hermes recommend, raising catalog page size, or browser `prompt`/`confirm`/`alert` for add, edit, or delete.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Keyword search | `GET /api/v1/books?q=Hobbit` | 200; match title, author, summary, ISBN, or `genres_tags` | `[]` if none |
| Multi-filter | `?genre=Fantasy&format=physical&room=Office&status=reading` | 200; AND of all provided filters | Unset ignored; invalid `status` → 422 |
| Status filter | `status=available\|reading\|finished` | Derived from sessions (see Design Notes) | Finished-only books are `available` |
| Manual create | `POST /books` `{title, author}` with ISBN service down | 201; no ISBN HTTP call | 422 if title or author missing |
| ISBN prefill | `GET /isbn/{isbn}` Open Library hit | 200 dict of metadata fields; not auto-saved | 404 on miss/network; UI warns and copies ISBN into the manual form |
| Edit / delete | `PUT /books/{id}` partial; `DELETE /books/{id}` after Vuetify confirm | 200 updated fields; 204 and sessions cascade | 404 if missing; cancel leaves book |

</frozen-after-approval>

## Code Map

- `app/services/book_service.py` -- `list_books` L20–49 filters `query`/`genre`/`room` only; `q` skips `genres_tags`. Add `format` ILIKE and `status` via session join. `create_book` L6–12 is ISBN-isolated. `update_book` L52–60 uses `exclude_unset`. `delete_book` L63–70 already cascades sessions.
- `app/api/books.py` -- `list_books` L21–37: add `format` and `status` query params. Leave CRUD and `GET /{id}/sessions` L95–136 in place.
- `app/models.py` -- `Book`/`BookCreate`/`BookUpdate`/`BookRead` L10–105. Create requires `title`+`author`. `formats` is a string (default `"physical"`). No `Book.status` column.
- `app/api/isbn.py` + `app/services/isbn_service.py` -- Open Library only (`lookup_isbn` L5–73); `None` → 404. Add a Pydantic response model; never import this from `create_book`.
- `frontend/src/services/api.js` -- `getBooks(params)` L17–19 already forwards query params. `updateBook` L26–28 exists but is unused in UI.
- `frontend/src/App.vue` -- bar L76–115 is `q` + `genre` only. `handleFilterRoom` L360–364 stuffs room into `q` — pass `room`. Add format + status controls.
- `frontend/src/components/AddBookDialog.vue` -- ISBN is advisory (L258–286). `submit` L288–302 skips `formRef` validate and only `console.error`s. No Save & Add Next. Format items L173 are `physical, pdf, epub, audiobook` — align to `physical, kindle, epub, pdf`.
- `frontend/src/components/BookDetailDialog.vue` -- read-only; delete uses `confirm()` L239–250. Add edit via `updateBook` (reuse AddBookDialog or inline fields) and a Vuetify confirm dialog.
- `frontend/src/components/BookCard.vue` -- cover/location/active-reader chips already present; no filter work needed.
- `frontend/src/components/ShelfManager.vue` -- keep `filter-room` emit; wire it to `room` on `getBooks`.
- `tests/test_api.py` -- CRUD/`q` covered L45–88. Put new filter/ISBN/cascade cases in `tests/test_catalog_and_isbn.py`.
- Read-only: `app/api/readers.py`, `frontend/src/components/ReaderTracker.vue`.

## Tasks & Acceptance

**Execution:**
- [x] `app/services/book_service.py` + `app/api/books.py` -- AND filters for `format` and `status` (`available`\|`reading`\|`finished`); include `genres_tags` in `q`; 422 on invalid `status` -- Completes FR-2 on the list endpoint
- [x] `app/api/isbn.py` -- Pydantic response model for the lookup dict; keep 404 on miss/network -- Accurate OpenAPI without breaking isolation
- [x] `frontend/src/App.vue` -- Format and status filter controls; pass `q`/`genre`/`format`/`room`/`status`; map ShelfManager `filter-room` to `room` -- UJ-2 browse
- [x] `frontend/src/components/AddBookDialog.vue` -- Validate title/author; snackbar/alert on create failure; Save & Add Next (persist, reset, keep open); format items `physical`/`kindle`/`epub`/`pdf`; ISBN stays advisory -- FR-5/FR-6
- [x] `frontend/src/components/BookDetailDialog.vue` -- Edit via `PUT`; Vuetify delete confirm (no `confirm()`); refresh catalog on success -- FR-1 edit and FR-4
- [x] `tests/test_catalog_and_isbn.py` -- Matrix cases: AND filters, `q` hits tags, status derivation, create does not call ISBN, ISBN 200/404 with httpx mocked, delete cascades, invalid status 422 -- Locks edges

**Acceptance Criteria:**
- Given mixed formats, rooms, tags, and session states, when keyword + genre + format + room + status are applied together, then only books matching every selected filter appear.
- Given book detail, when title/author/location are edited and saved, then the card and detail show the new values without a full page reload.
- Given Add Book, when ISBN lookup fails, then the user can still type and save; when it succeeds, fields are prefilled and remain editable.
- Given a stack of books, when Save & Add Next is used, then the first book is persisted and the dialog stays open on a blank form.
- Given `pytest tests/`, existing reader tests and the new catalog/ISBN tests all pass.

## Spec Change Log

## Design Notes

Catalog `status` is derived from `ReadingSession`, not stored on `Book`:

- `reading` — ≥1 session with `status == "reading"`
- `finished` — ≥1 `finished` session and none `reading`
- `available` — no `reading` session (never-started and finished-only)

Do not add `Book.status`. Create must not import or call `lookup_isbn`.

## Verification

**Commands:**
- `pytest tests/test_catalog_and_isbn.py tests/test_api.py tests/test_readers_and_sessions.py -q` -- expected: all pass
- `python -c "from app.main import app"` -- expected: imports without error

## Suggested Review Order

**Catalog list filters**

- Derived status and AND filters live here, not on `Book`.
  [`book_service.py:27`](../../app/services/book_service.py#L27)

- Query aliases `format`/`status`; invalid status is 422 via Literal.
  [`books.py:19`](../../app/api/books.py#L19)

**ISBN isolation**

- Create never calls lookup; comment is the invariant.
  [`book_service.py:6`](../../app/services/book_service.py#L6)

- Advisory OpenAPI model; 404 still means miss or network.
  [`isbn.py:9`](../../app/api/isbn.py#L9)

**Catalog UI**

- Format, status, and trimmed room params go to `getBooks`.
  [`App.vue:353`](../../frontend/src/App.vue#L353)

- Shelf clicks set `room`, not keyword `q`.
  [`App.vue:420`](../../frontend/src/App.vue#L420)

**Dual ingestion**

- ISBN prefill stays editable, including `formats`.
  [`AddBookDialog.vue:277`](../../frontend/src/components/AddBookDialog.vue#L277)

- Save & Add Next persists, resets, keeps the dialog open.
  [`AddBookDialog.vue:369`](../../frontend/src/components/AddBookDialog.vue#L369)

- Re-entry guard and null coercion prevent double-create/422.
  [`AddBookDialog.vue:329`](../../frontend/src/components/AddBookDialog.vue#L329)

**Edit and delete**

- Inline edit via `PUT`; empty fields become null.
  [`BookDetailDialog.vue:394`](../../frontend/src/components/BookDetailDialog.vue#L394)

- Vuetify confirm replaces browser `confirm()`.
  [`BookDetailDialog.vue:268`](../../frontend/src/components/BookDetailDialog.vue#L268)

- Stored non-standard formats stay selectable on edit.
  [`BookDetailDialog.vue:309`](../../frontend/src/components/BookDetailDialog.vue#L309)

**Tests**

- AND filters use a non-unique `q` so format cannot be a no-op.
  [`test_catalog_and_isbn.py:91`](../../tests/test_catalog_and_isbn.py#L91)

- Status derivation, ISBN advisory-only, cascade delete, partial PUT.
  [`test_catalog_and_isbn.py:157`](../../tests/test_catalog_and_isbn.py#L157)
