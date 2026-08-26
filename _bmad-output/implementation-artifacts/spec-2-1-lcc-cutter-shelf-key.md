---
title: 'LCC Cutter shelf-key badge'
type: 'feature'
created: '2026-08-26'
status: 'done'
review_loop_iteration: 0
context: []
baseline_commit: 'f795fd80302e2f29b92507cabe8c08a12338e2b9'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Books have no shelf-key call number, and many titles have no ISBN, so classification cannot depend on ISBN lookup.

**Approach:** Add a small heuristic genre→LCC-letter table plus a simplified Cutter-code algorithm; expose a suggest-then-confirm flow (compute suggestion, human approves/edits before persisting) via a new endpoint; persist into the existing `lcc_call_number`/`cutter_number` columns; show the combined call number as a badge on the book card.

## Boundaries & Constraints

**Always:**
- Classification must be computable from title, `genres_tags`, and structured authors alone — never require or call ISBN lookup (`app/services/isbn_service.py` stays untouched).
- The genre-map and Cutter-digit tables are heuristic, checked-in constants (single module) — deterministic for the same input, not required to match real LCC/Cutter-Sanborn authority tables.
- Zero authors → Cutter off the title. Exactly one author → Cutter off that author's `last_name`. Multiple authors → caller must supply `primary_author_id`; do not silently default to the first author.
- A suggestion is never auto-persisted — it is only written to `Book.lcc_call_number`/`cutter_number` via the existing `PUT /books/{id}` update path, after human confirmation.
- No genre match → fall back to a single documented default class (e.g. general literature), not an error.

**Ask First:** None — open questions were resolved before this spec (suggest-then-confirm flow, title-Cutter for zero authors, user-chosen primary author for multiple, full call number badge, small heuristic map).

**Never:**
- Never build or import a real/authoritative LCC or Cutter-Sanborn table — heuristic only.
- Never touch `BookCreate` or the create-book path — classification is a distinct, post-save action, not part of book creation.
- Never require an ISBN or call `/isbn/{code}` from classification code.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Zero authors | Book with no linked authors | Suggestion uses title for Cutter source | N/A |
| Single author | Book with exactly one author | Suggestion uses that author's last name, no `primary_author_id` needed | N/A |
| Multiple authors, no choice given | Book with 2+ authors, request omits `primary_author_id` | 422 response listing the book's authors (id + display name) so the client can prompt | Client shows author picker, retries with `primary_author_id` |
| Multiple authors, choice given | `primary_author_id` matches a linked author | Suggestion uses that author's last name | N/A |
| `primary_author_id` not linked to book | id doesn't match any linked author | 400 error | Client surfaces error, re-prompts |
| No genre match | `genres_tags` empty or no keyword hits | Falls back to documented default LCC class | N/A |
| Confirm | User edits suggested fields, submits | `PUT /books/{id}` with edited `lcc_call_number`/`cutter_number`; badge appears on card | Existing update-validation errors apply |

</frozen-after-approval>

## Code Map

- `app/models.py:40-41` -- `lcc_call_number`/`cutter_number` already on `Book` (uncommitted); add both (optional) to `BookUpdate` (~144-159) and `BookRead` (~162-179).
- `app/services/book_service.py:169-199` -- `to_book_read()`: populate the two new fields from `book.*`.
- `app/services/classification_service.py` -- NEW: `GENRE_LCC_MAP`, `CUTTER_DIGIT_TABLE`, `suggest_lcc_class(genres_tags)`, `suggest_cutter(source_text)`, `suggest_classification(book, authors, primary_author_id)`.
- `app/api/books.py:20-90` -- add `POST /books/{book_id}/classification/suggest`, reusing `book_service.get_book` + `book_service.list_book_authors` for 404/authors lookup.
- `frontend/src/services/api.js:26-30` -- add `suggestClassification(bookId, primaryAuthorId)` next to `updateBook`.
- `frontend/src/components/BookDetailDialog.vue:146-157` -- add a "Classify" button near the existing chip row; opens the new dialog; on confirm, reuse the existing `api.updateBook` + `refresh` emit pattern (see `~482`).
- `frontend/src/components/ClassifySuggestDialog.vue` -- NEW: author picker (reuse author list shape from `AuthorRows.vue`/`authors.js`) when `book.authors.length > 1`, editable call-number fields, confirm/cancel.
- `frontend/src/components/BookCard.vue:24-34` -- add a call-number `v-chip` (same shape as the `locationDisplay` chip), `v-if` guarded on both fields being present.
- `tests/test_catalog_and_isbn.py` or new `tests/test_classification.py` -- follow existing `TestClient` + JSON payload pattern.

## Tasks & Acceptance

**Execution:**
- [x] `app/services/classification_service.py` -- write `GENRE_LCC_MAP` (~10-15 keyword entries + default), `CUTTER_DIGIT_TABLE`, and the three suggest functions -- pure, deterministic, no DB/network access
- [x] `app/models.py` -- add `lcc_call_number`/`cutter_number` (both `Optional[str] = None`) to `BookUpdate` and `BookRead`; add `ClassificationSuggestion` and `ClassificationSuggestRequest` schemas -- exposes fields for confirm/badge
- [x] `app/services/book_service.py` -- populate the two fields in `to_book_read()` -- badge data reaches the client
- [x] `app/api/books.py` -- add `POST /books/{book_id}/classification/suggest`: 404 if book missing, 422-with-author-list if 2+ authors and no `primary_author_id`, 400 if `primary_author_id` doesn't belong to the book, else return `ClassificationSuggestion` -- implements suggest-then-confirm
- [x] `frontend/src/services/api.js` -- add `suggestClassification(bookId, primaryAuthorId)` -- client hook for the new endpoint
- [x] `frontend/src/components/ClassifySuggestDialog.vue` -- new dialog: author picker when needed, editable suggested fields, confirm calls `api.updateBook` -- human-in-the-loop confirm step
- [x] `frontend/src/components/BookDetailDialog.vue` -- wire a "Classify" trigger into the existing chip/action area -- entry point for the flow
- [x] `frontend/src/components/BookCard.vue` -- add the call-number badge chip -- visible shelf-key on the catalog card
- [x] `tests/test_classification.py` -- cover every row of the I/O matrix above -- locks in edge-case behavior

**Acceptance Criteria:**
- Given a book with no authors and genre "History", when classification is suggested, then the Cutter source is the title and the class matches the History mapping entry.
- Given a book with two authors and no `primary_author_id`, when classification is suggested, then the API returns 422 with the book's author list.
- Given a confirmed suggestion, when the user submits it, then `GET /books/{id}` reflects the new `lcc_call_number`/`cutter_number` and the book card shows the badge.
- Given a book with neither field set, when the card renders, then no call-number chip appears.

## Design Notes

Cutter algorithm (illustrative, not exhaustive): take the source string (author last name or title), strip non-letters, uppercase the first letter, then map each subsequent letter through `CUTTER_DIGIT_TABLE` (a-z → 2-9 in fixed groups, e.g. vowels get low digits, consonant clusters get higher ones) until 2 digits are produced, e.g. `"Orwell"` → `"O74"`. Exact digit assignments are an implementation choice — keep them in one table so they're easy to inspect/adjust later.

## Verification

**Commands:**
- `pytest tests/test_classification.py -v` -- expected: all new edge-case tests pass
- `pytest` -- expected: full suite still green (no regression in existing book CRUD/ISBN tests)

**Manual checks (if no CLI):**
- In the running app, open a multi-author book, trigger Classify, confirm the author picker appears and a badge shows on the card after confirming.

## Suggested Review Order

**Entry point**

- New endpoint: loads the book/authors, delegates to the heuristic service, maps its errors to 404/422/400.
  [`books.py:110`](../../app/api/books.py#L110)

**Classification heuristic**

- Combines class + Cutter into one suggestion; pure and deterministic, nothing persisted here.
  [`classification_service.py:167`](../../app/services/classification_service.py#L167)

- Author-selection rule: title for zero authors, sole author for one, explicit choice required for multiple — now validated in all three branches.
  [`classification_service.py:139`](../../app/services/classification_service.py#L139)

- Genre keyword table checked in order so multi-word entries win over the single words they contain.
  [`classification_service.py:27`](../../app/services/classification_service.py#L27)

- Simplified Cutter code: first letter + two digits from a hand-written a-z table, corrected docstring example.
  [`classification_service.py:87`](../../app/services/classification_service.py#L87)

- Ambiguous/invalid-author signals surfaced as typed exceptions the API layer maps to HTTP status codes.
  [`classification_service.py:123`](../../app/services/classification_service.py#L123)

**API contract & persistence**

- New request/response shapes for the suggest endpoint; kept separate from `BookCreate` per the "never touch create" boundary.
  [`models.py:186`](../../app/models.py#L186)

- `lcc_call_number`/`cutter_number` exposed on `BookUpdate` (confirm path) and `BookRead` (badge data).
  [`models.py:160`](../../app/models.py#L160)

- `to_book_read` wired to surface the two persisted fields to every book-read consumer.
  [`book_service.py:200`](../../app/services/book_service.py#L200)

**Suggest-then-confirm UI**

- Open handler now shows the already-saved call number instead of silently recomputing over it.
  [`ClassifySuggestDialog.vue:188`](../../frontend/src/components/ClassifySuggestDialog.vue#L188)

- Confirm trims both fields before persisting via the existing `PUT /books/{id}`.
  [`ClassifySuggestDialog.vue:162`](../../frontend/src/components/ClassifySuggestDialog.vue#L162)

- 422 response drives the author-picker branch; any other error surfaces inline.
  [`ClassifySuggestDialog.vue:139`](../../frontend/src/components/ClassifySuggestDialog.vue#L139)

- "Classify" entry point wired into the existing chip/action row, reusing the `refresh` emit pattern.
  [`BookDetailDialog.vue:171`](../../frontend/src/components/BookDetailDialog.vue#L171)

- Client hook for the new endpoint; `!= null` check preserves a falsy-but-valid author id of `0`.
  [`api.js:35`](../../frontend/src/services/api.js#L35)

**Badge display**

- Call-number chip follows the existing location-chip shape, guarded on both fields being present.
  [`BookCard.vue:44`](../../frontend/src/components/BookCard.vue#L44)

**Peripherals**

- Legacy-DB upgrade path: adds the two columns and their indexes so an upgraded database matches a fresh schema.
  [`database.py:108`](../../app/database.py#L108)

- Full I/O-matrix coverage plus the three added primary-author-id edge cases.
  [`test_classification.py:1`](../../tests/test_classification.py#L1)

- Extended to assert the ALTER-TABLE path actually adds the new columns and indexes on a legacy table.
  [`test_authors_and_publishers.py:336`](../../tests/test_authors_and_publishers.py#L336)
