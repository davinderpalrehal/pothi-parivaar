---
title: 'Author publisher persistence'
type: 'feature'
created: '2026-08-23'
status: 'done'
review_loop_iteration: 0
baseline_commit: '5c67d108bce46c183816ce85092f03d352e6dc04'
context:
  - '_bmad-output/specs/spec-structured-authors/SPEC.md'
  - '_bmad-output/specs/spec-structured-authors/name-rules.md'
  - '_bmad-output/specs/spec-structured-authors/publishers.md'
  - '_bmad-output/specs/spec-structured-authors/brownfield.md'
  - 'AGENTS.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Books store one `author` string, so multiple authors, full names, and publishers cannot be found as their own records. Existing rows are already saved as short forms like `D. Carnegie`.

**Approach:** Add first-class author and publisher records, link them to books, migrate existing `author` strings once with `name-rules.md`, and keep a derived `author` short form on reads so current catalog cards and Hermes keep working. Do not change Add Book / Book Detail forms in this story.

## Boundaries & Constraints

**Always:**
- FastAPI + Pydantic v2, SQLite WAL (`data/pothi.db`), `/api/v1/`, Vue 3 + Vuetify 3 unchanged this story.
- Author: required first name; last name required and may be a single space (mononym); optional middle. Same first+middle+last reuses one author.
- Book may have zero or more authors; order is display/save order.
- Publisher is its own record with one organization name; a book may have zero or one; same name reuses one publisher.
- Title remains required. Authors and publisher are optional.
- Split and short form follow `name-rules.md`. Mononym display is `Plato`, not `P.`.
- One-time migration converts every existing `Book.author` string. Empty string → zero authors. `D. Carnegie` → first=`D.`, last=`Carnegie`.
- Keyword search and Hermes locate match first, middle, last, and derived short form.
- Reads still include a derived `author` string (comma-separated short forms) so existing Vue/Hermes keep rendering.
- Work on a feature branch from `main`, not on `main`.

**Ask First:**
- Dropping the `Book.author` column instead of leaving it unused after migration.
- More than one publisher per book.
- Attaching publishers during ISBN lookup.

**Never:**
- Add Book / Book Detail field changes (story 1.2).
- ISBN name-split rewrite (story 1.3).
- Author or publisher browse UI.
- Inventing `Dale` from `D. Carnegie`.
- Creating publishers from ISBN or from the author migration.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Two authors | POST book with Dale Carnegie + Jane Doe | 201; two author records in order; read `author` is `D. Carnegie, J. Doe` | 422 if an author is missing first name |
| Magazine | POST title only, no authors, optional publisher name | 201; zero authors; publisher linked if named | Title missing → 422 |
| Mononym | Author first=`Cher`, last=` ` | Stored; read `author` is `Cher` | Last omitted → 422 (space is the mononym form) |
| Reuse | Second book with same name parts / publisher name | Same author / publisher id | N/A |
| Migration | Existing `D. Carnegie` and `A, B` rows | Script applies `name-rules.md`; books searchable by parts | Empty author → zero authors |
| Search | `GET /books?q=Dale` or `q=D. Carnegie` | 200; matches name parts and short form | `[]` if none |

</frozen-after-approval>

## Code Map

- `app/models.py` -- `Book.author` is the current required string; add Author, Publisher, and book-author link; BookCreate/Update/Read gain structured authors and optional publisher while Read keeps derived `author`.
- `app/services/book_service.py` -- create/update/list/get persist links, reuse by name, search name parts + short form, stop treating `Book.author` as source of truth.
- `app/api/books.py` -- list `q` and CRUD schemas follow the new write shape; derived `author` stays on responses.
- `app/api/hermes.py` -- locate/recommend still return `author`; locate matches name parts + short form.
- `app/services/isbn_service.py` -- leave join-to-string as-is this story.
- `frontend/src/components/*.vue` -- do not change forms; they keep reading `book.author`.
- `tests/test_api.py` / `tests/test_catalog_and_isbn.py` -- create still needs title; author no longer required. Add persistence/migration/search cases.

## Tasks & Acceptance

**Execution:**
- [x] `app/models.py` -- Author, Publisher, book-author order, optional publisher on book; Read keeps derived `author` -- CAP-1, CAP-6, CAP-8
- [x] `app/services/book_service.py` + `app/api/books.py` -- write structured authors/publisher; search name parts + short form; title-only create -- CAP-2, CAP-4
- [x] `app/api/hermes.py` -- locate/recommend use derived `author` and name-part match -- CAP-4
- [x] one-time migration -- apply `name-rules.md` to existing `Book.author` values -- CAP-7
- [x] `tests/` -- matrix: two authors, magazine, mononym, reuse, migration, `q` hits first name and short form -- locks edges

**Acceptance Criteria:**
- Given a two-author create, when the book is read, then both authors are stored in order and `author` is `D. Carnegie, J. Doe`.
- Given title only, when saved, then the book has zero authors and no publisher unless one was named.
- Given existing rows, when the one-time migration runs, then `D. Carnegie` becomes first=`D.` last=`Carnegie` and search still finds the book.
- Given two books with the same name parts, when saved, then they share one author record.
- Given `pytest tests/`, existing catalog/reader tests and the new author tests pass.

## Design Notes

Migration and new writes use the same split in `name-rules.md`. Leave `Book.author` populated with the derived short form after write/migration if that is the cheapest way to keep current Vue working — it is a projection, not the source of truth.

## Verification

**Commands:**
- `pytest tests/` -- expected: all pass, including new author/publisher/migration cases

## Dev Agent Record

**Implementation Plan:**
- Keep `Book.author` as a derived short-form projection so Vue cards and Hermes keep rendering.
- Accept structured `authors` / `publisher_name` on write, and still accept the legacy `author` string (split via `name-rules.md`) so Add Book / Book Detail stay unchanged.
- Reuse author and publisher rows by exact stored name parts; search and Hermes locate match first/middle/last plus the stored short form.
- Run one-time string conversion from `migrate_schema` after the new tables exist.

**Completion Notes:**
- Author, Publisher, and BookAuthor tables added; Book gained optional `publisher_id`.
- Create requires title only. Two-author create returns `D. Carnegie, J. Doe`. Mononym last name is a single space and displays as `Cher`.
- Same first+middle+last and same publisher name reuse one record.
- `migrate_book_author_strings` applies `name-rules.md` to existing `Book.author` values and is invoked from `migrate_schema` (idempotent; does not create publishers).
- Vue PUT that echoes the current derived `author` does not re-split stored name parts.

**Debug Log:**
- Empty-author books have no BookAuthor rows, so migration skip logic treats empty strings as already converted.
- Legacy reader-column migration fixtures have no `bookauthor` table; author conversion is skipped until that table exists.

## File List

- app/models.py
- app/services/name_rules.py
- app/services/book_service.py
- app/services/author_migration.py
- app/api/books.py
- app/api/hermes.py
- app/api/readers.py
- app/database.py
- tests/test_name_rules.py
- tests/test_authors_and_publishers.py
- tests/test_api.py
- tests/test_catalog_and_isbn.py
- _bmad-output/implementation-artifacts/1-1-author-publisher-persistence.md
- _bmad-output/implementation-artifacts/sprint-status.yaml

## Change Log

- 2026-08-23: Implemented author/publisher persistence, derived `author` reads, name-part search, and one-time author-string migration.

## Suggested Review Order

**Schema**

- First-class author records; `Book.author` is only a derived short-form projection.
  [`models.py:16`](../../app/models.py#L16)

- Optional publisher on a book, reused by organization name.
  [`models.py:11`](../../app/models.py#L11)

- Ordered book–author links; same author cannot appear twice on one book.
  [`models.py:42`](../../app/models.py#L42)

**Write path**

- Title-only create; structured authors and optional publisher persist as links.
  [`book_service.py:203`](../../app/services/book_service.py#L203)

- Same first+middle+last reuses one author row.
  [`book_service.py:55`](../../app/services/book_service.py#L55)

- Replace links in display order; first-seen de-dupe avoids a PK clash.
  [`book_service.py:109`](../../app/services/book_service.py#L109)

- Last name may be a single space (mononym); first name is required.
  [`models.py:86`](../../app/models.py#L86)

**Name rules**

- Split stored/API strings per `name-rules.md`, including trimmed comma segments.
  [`name_rules.py:17`](../../app/services/name_rules.py#L17)

- Catalog short form: `D. Carnegie`, or the first name as-is for a mononym.
  [`name_rules.py:46`](../../app/services/name_rules.py#L46)

**Reads and search**

- Reads recompute `author` plus nested `authors[]` and `publisher`.
  [`book_service.py:169`](../../app/services/book_service.py#L169)

- Keyword search hits first, middle, last, and the stored short form.
  [`book_service.py:154`](../../app/services/book_service.py#L154)

- Hermes locate uses the same name-part subquery; recommend still returns `author`.
  [`hermes.py:101`](../../app/api/hermes.py#L101)

**Migration**

- One-time conversion of existing `Book.author` strings; empty stays zero authors.
  [`author_migration.py:10`](../../app/services/author_migration.py#L10)

- Existing catalogs get `publisher_id` then run the string conversion.
  [`database.py:104`](../../app/database.py#L104)

**Tests**

- Matrix: two authors, magazine, mononym, reuse, migration, search, middle-name hit.
  [`test_authors_and_publishers.py:37`](../../tests/test_authors_and_publishers.py#L37)

- Name-rules examples and short-form display.
  [`test_name_rules.py:9`](../../tests/test_name_rules.py#L9)
