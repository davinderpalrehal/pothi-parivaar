---
title: 'Author publisher persistence'
type: 'feature'
created: '2026-08-23'
status: 'ready-for-dev'
review_loop_iteration: 0
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
- [ ] `app/models.py` -- Author, Publisher, book-author order, optional publisher on book; Read keeps derived `author` -- CAP-1, CAP-6, CAP-8
- [ ] `app/services/book_service.py` + `app/api/books.py` -- write structured authors/publisher; search name parts + short form; title-only create -- CAP-2, CAP-4
- [ ] `app/api/hermes.py` -- locate/recommend use derived `author` and name-part match -- CAP-4
- [ ] one-time migration -- apply `name-rules.md` to existing `Book.author` values -- CAP-7
- [ ] `tests/` -- matrix: two authors, magazine, mononym, reuse, migration, `q` hits first name and short form -- locks edges

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
