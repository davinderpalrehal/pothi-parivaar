---
title: 'Author honorific short form and editor'
type: 'feature'
created: '2026-09-02'
status: 'done'
review_loop_iteration: 0
baseline_commit: 'b0b794c9d9e8b828727e51ba72072a442c8b3beb'
context:
  - '_bmad-output/specs/spec-structured-authors/SPEC.md'
  - '_bmad-output/specs/spec-structured-authors/name-rules.md'
  - '_bmad-output/specs/spec-structured-authors/honorifics.md'
  - '_bmad-output/implementation-artifacts/epic-1-context.md'
  - 'AGENTS.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Catalog cards treat titles as the given name, so `Dr. Davinder Singh` becomes `D. Singh` and `Bhai Sahib Bhai Vir Singh ji` becomes something like `B. ji`. New titles appear in daily use; they must not wait on a deploy.

**Approach:** Keep titles in first/middle/last. Derive short form by peeling a persisted honorific list from the reconstructed tokens. Seed that list from `honorifics.md` and let any household member add/edit/disable/delete rows in the app.

## Boundaries & Constraints

**Always:**
- Vue 3 + Vuetify 3. Short form from `name-rules.md`; seed + editor contract from `honorifics.md`.
- No title columns. Identity remains exact first+middle+last. Do not re-run the CAP-7 author-string migration.
- `split_author_string` stays comma-then-space. Honorifics affect derived short form, `Book.author` projection, and search against that projection — not stored name parts.
- Longest token match, case-insensitive, optional trailing period. Prefixes peel front; suffixes peel end. Empty abbreviation omits (e.g. `ji`).
- Duplicate tokens+role rejected. Empty tokens rejected. Disabled rows ignored. List changes refresh every book’s denormalized `author` string from current name parts.
- No auth/roles. Branch `feat/author-honorifics`.

**Ask First:**
- Treating Singh, Kaur, or Guru as honorifics. Moving titles into their own columns.

**Never:**
- ISBN split rewrite (story 1.3). Inventing given names from initials. Custom CSS. Second rewrite of first/middle/last. Author-browse UI.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Doctor | first=`Dr.`, middle=`Davinder`, last=`Singh` | Card `Dr. D. Singh` | N/A |
| BHB + ji | first=`Bhai`, middle=`Sahib Bhai Vir Singh`, last=`ji` | Card `BHB V. Singh` | N/A |
| Unchanged core | Dale / Carnegie | Card `D. Carnegie` | N/A |
| Mononym | Plato, last=` ` | Card `Plato` | N/A |
| Search abbrev | q=`BHB` after save | Book found | N/A |
| Add honorific | New prefix tokens+abbrev via editor | Next card uses it; name parts unchanged | Duplicate tokens+role 409/422 |
| Disable row | Disable `Bhai Sahib Bhai` | Card no longer uses `BHB` | N/A |

</frozen-after-approval>

## Code Map

- `app/services/name_rules.py` -- `author_short_form` `:46-52` ignores middle and honorifics; `joined_short_forms` `:55-59` must pass middle. Extend short form to accept a honorific list (or load inside). Keep `split_author_string` `:17-43`.
- `app/services/book_service.py` -- `_replace_book_authors` `:112-125` and `to_book_read` `:172-188` already project `joined_short_forms`; pass loaded honorifics. `list_books` `:254-264` ILIKE `Book.author` plus name parts — abbreviations only match after projection refresh.
- `app/models.py` -- `Author` `:16-20` unchanged. Add honorific table (tokens, role prefix|suffix, abbreviation, enabled) mirroring `Location` `:75-79`.
- `app/database.py` `migrate_schema` `:27-139` -- create table + seed if empty from `honorifics.md` (copy seed rows; do not parse markdown at runtime if a Python seed tuple list is easier — values must match the companion).
- `app/api/locations.py` + `app/main.py` `:45-56` -- copy CRUD mount pattern for honorifics (list, create, update/disable, delete).
- `app/services/location_service.py` -- upsert/duplicate style for tokens+role uniqueness.
- `frontend/src/App.vue` -- `currentView` `:331`, drawer `:13-38`, tabs `:50-55`, panels `:74-282`, bottom nav `:287-304`. No vue-router.
- `frontend/src/components/ShelfManager.vue` -- list + dialog pattern for the editor.
- `frontend/src/services/api.js` -- locations `:80-86`; add honorific client methods.
- `tests/test_name_rules.py` -- extend short-form cases; keep existing split assertions.
- `tests/test_authors_and_publishers.py` -- create/search still pass; add Dr./BHB create+search.
- `_bmad-output/specs/spec-structured-authors/honorifics.md` -- seed rows; read-only contract.

## Tasks & Acceptance

**Execution:**
- [x] `app/services/name_rules.py` -- reconstruct tokens, peel persisted list, emit short form including middle in the sequence -- CAP-3
- [x] `app/models.py` + `app/database.py` + honorific service/API -- table, seed, CRUD, refresh `Book.author` on list change -- CAP-9
- [x] `app/main.py` + `app/services/book_service.py` -- mount router; load list when deriving/searching -- CAP-3, CAP-4
- [x] `frontend/src/App.vue` + editor component + `api.js` -- household honorific list UI -- CAP-9
- [x] `tests/test_name_rules.py` + `tests/test_authors_and_publishers.py` -- matrix rows including search `BHB` -- CAP-3, CAP-4, CAP-9

**Acceptance Criteria:**
- Given stored `Dr.` / `Davinder` / `Singh`, when the catalog renders, then the card shows `Dr. D. Singh`.
- Given stored Bhai Sahib Bhai Vir Singh ji parts, when rendered, then the card shows `BHB V. Singh`.
- Given a new honorific saved in the editor, when a matching author is shown, then the new abbreviation appears and first/middle/last are unchanged.
- Given `q=BHB` after that author is saved, when searching, then the book is returned.

## Spec Change Log

## Design Notes

`author_short_form` today uses only first+last, so `Dr.`+`Davinder`+`Singh` becomes `D. Singh` (first character of `Dr.`). Rebuild `[first] + middle tokens + [last unless space]`, peel, then initial+family on what remains.

When the honorific list changes, rewrite `Book.author` for every book from linked name parts so ILIKE search sees `BHB` without touching Author rows.

## Verification

**Commands:**
- `python -m pytest tests/test_name_rules.py tests/test_authors_and_publishers.py -q` -- expected: pass
- `cd frontend && npm test -- --run src/utils/authors.test.js` -- expected: pass (payload tests unchanged)

**Manual checks (if no CLI):**
- Add Book `Dr.` / `Davinder` / `Singh` → card `Dr. D. Singh`. Open honorifics view, add a prefix, confirm a matching card updates without editing the author.

## Suggested Review Order

**Short form peel**

- Reconstruct first+middle+last, peel longest honorifics, then initial + family.
  [`name_rules.py:138`](../../app/services/name_rules.py#L138)

**Persistence and search projection**

- Honorific rows stay off the Author table; identity is still first+middle+last.
  [`models.py:82`](../../app/models.py#L82)

- Rewrite every `Book.author` from linked name parts when the list changes.
  [`honorific_service.py:78`](../../app/services/honorific_service.py#L78)

- Seed once if empty, then always refresh projections on migrate.
  [`database.py:152`](../../app/database.py#L152)

**Household editor**

- CRUD at `/honorifics`; duplicates 409, blank tokens 422.
  [`honorifics.py:16`](../../app/api/honorifics.py#L16)

- Mount next to locations on both `/api/v1` and `/api`.
  [`main.py:48`](../../app/main.py#L48)

- Honorifics view: add, edit, disable, confirm-delete.
  [`HonorificManager.vue:1`](../../frontend/src/components/HonorificManager.vue#L1)

- New App view (drawer, tab, bottom nav).
  [`App.vue:60`](../../frontend/src/App.vue#L60)

**Tests**

- Pure peel cases including Dr. and BHB.
  [`test_name_rules.py:75`](../../tests/test_name_rules.py#L75)

- Create, search `BHB`, CRUD refresh, migrate stale projection.
  [`test_authors_and_publishers.py:464`](../../tests/test_authors_and_publishers.py#L464)

