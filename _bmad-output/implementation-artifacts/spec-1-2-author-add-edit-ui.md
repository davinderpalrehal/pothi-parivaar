---
title: 'Author add edit UI'
type: 'feature'
created: '2026-08-25'
status: 'done'
review_loop_iteration: 0
baseline_commit: '96ffcdfece431995db7dddbebdaecb8882fa883e'
context:
  - '_bmad-output/specs/spec-structured-authors/SPEC.md'
  - '_bmad-output/specs/spec-structured-authors/name-rules.md'
  - '_bmad-output/implementation-artifacts/epic-1-context.md'
  - 'AGENTS.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Add Book and Book Detail still require one author string, so family members cannot enter first/middle/last, multiple authors, or a title with no authors, even though the API already stores structured authors.

**Approach:** Replace that field with zero or more author rows (first, last, optional middle). Saves send `authors[]` only. Cards keep the API’s derived `author` short form.

## Boundaries & Constraints

**Always:**
- Vue 3 + Vuetify 3. Write `authors: [{first_name, last_name, middle_name?}]`. Title required. Authors optional.
- Each kept row needs first and last. Last may be one space (mononym). Drop empty extra rows; do not POST blanks.
- Zero authors is valid. Row order is save/display order.
- Cards and read-only detail keep `book.author`. Edit hydrates from `book.authors[]`. Mononym last=` ` displays as Cher, not `C.`.
- Omit legacy `author` from create/update payloads.
- Branch `feat/1-2-author-add-edit-ui`.

**Ask First:**
- Author-browse UI. Changing how short form is derived.

**Never:**
- Publisher field this story (deferred). ISBN name split (story 1.3). Lookup may fill title/year/ISBN only.
- Inventing given names from initials. Custom CSS. ISBN from POST `/books`. Persistence/migration API changes.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Two authors | Dale/Carnegie then Jane/Doe, save | Order kept; card `D. Carnegie, J. Doe` | Incomplete kept row blocks save |
| Magazine | Title, zero author rows | Saves with zero authors | Missing title still blocks |
| Mononym | First=`Cher`, last=` ` | Card shows `Cher` | Last missing on a kept row blocks save |
| Edit hydrate | Detail edit of two authors | Rows match stored parts, not the short form | N/A |
| Remove author | Delete one of two rows, save | The other remains | N/A |

</frozen-after-approval>

## Code Map

- `frontend/src/components/AddBookDialog.vue` -- `form.author` field (~L90–96), required check (~L411–417), `createPayload()` (~L385–403). Repeatable rows; POST `authors`; stop sending `author`. ISBN `form.author = data.author` (~L364): remove or ignore; do not split.
- `frontend/src/components/BookDetailDialog.vue` -- edit `editForm.author` (~L25–31); keep read-only `{{ book.author }}` (~L149). `startEdit()` (~L423) hydrate from `book.authors[]`. `updatePayload()` / `saveEdit()` (~L442–484) drop author-required and legacy `author`.
- `frontend/src/components/BookCard.vue` -- `{{ book.author }}` (~L21); leave as derived short form.
- `app/models.py` -- `AuthorInput` / `BookCreate` / `BookUpdate` already match; `last_name` may be `" "`.
- `app/services/name_rules.py` -- server short form / `MONONYM_LAST`; UI posts `" "` for mononym last name.
- `app/api/isbn.py` -- `author` stays a string; no split.

## Tasks & Acceptance

**Execution:**
- [x] `frontend/src/components/AddBookDialog.vue` -- author rows; POST `authors` only; zero authors allowed -- CAP-1, CAP-2
- [x] `frontend/src/components/BookDetailDialog.vue` -- same; hydrate `authors[]`; PUT without `author`; read mode keeps `book.author` -- CAP-1, CAP-2, CAP-3
- [x] `frontend/src/components/BookCard.vue` -- no change unless it still assumes a required author string -- CAP-3

**Acceptance Criteria:**
- Given two complete authors on Add Book, when saved, then the card shows `D. Carnegie, J. Doe` and edit shows two full-name rows.
- Given title and no author rows, when saved, then the book has zero authors.
- Given Cher with last name a single space, when saved, then the card shows `Cher`.
- Given a two-author book, when Detail edit opens, then fields come from `authors[]` not the derived short form.

## Spec Change Log

## Design Notes

Mirror location `v-row` / `v-col` for First, Middle, Last plus add/remove. User types a space in last for a mononym. Do not send `author` on write — echoing the short form on PUT re-splits `D. Carnegie`.

## Verification

**Commands:**
- `pytest tests/` -- expected: existing API tests still pass
- `node --test frontend/src/utils/authors.test.js` -- expected: matrix rows pass (two authors, magazine, mononym, hydrate, remove, incomplete row)

**Manual checks (if no CLI):**
- Add Book and Book Detail: two authors, magazine, Cher, remove-one on edit.
- ISBN lookup does not fill author rows this story.

## Suggested Review Order

**Write payload**

- Drop empty rows and never send the derived `author` string.
  [`authors.js:47`](../../frontend/src/utils/authors.js#L47)

- Add Book POST uses `authors[]` only.
  [`AddBookDialog.vue:381`](../../frontend/src/components/AddBookDialog.vue#L381)

- Detail PUT hydrates name parts then sends `authors[]`.
  [`BookDetailDialog.vue:417`](../../frontend/src/components/BookDetailDialog.vue#L417)

**UI rows**

- Repeatable First/Middle/Last with stable keys.
  [`AuthorRows.vue:10`](../../frontend/src/components/AuthorRows.vue#L10)

- ISBN lookup still skips author rows this story.
  [`AddBookDialog.vue:351`](../../frontend/src/components/AddBookDialog.vue#L351)

**Derived display**

- Cards still render the server short form.
  [`BookCard.vue:21`](../../frontend/src/components/BookCard.vue#L21)

**Tests**

- Matrix coverage for payload, magazine, mononym, hydrate.
  [`authors.test.js:12`](../../frontend/src/utils/authors.test.js#L12)

