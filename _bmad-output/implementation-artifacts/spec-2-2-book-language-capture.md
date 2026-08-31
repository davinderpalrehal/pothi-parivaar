---
title: 'Book language capture (story 2.2)'
type: 'feature'
created: '2026-08-31'
status: 'done'
review_loop_iteration: 0
baseline_commit: 'a2a55e8d64c54e0b4a1aa2650f05fbd81355cb01'
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Books carry no language anywhere in the system, so the collection cannot be grouped or filtered by the axis that matters most for shelving it — the library is Sikh/Punjabi-heavy. Language cannot be inferred: every title is in Latin script, romanized Punjabi included.

**Approach:** Give `Book` a primary language (ISO 639-3) plus optional additional languages, enterable on the add and edit forms, filterable through the books API, and visible as a chip on the catalog card.

## Boundaries & Constraints

**Always:**
- Language is entered by a human, **never guessed**. No script heuristic, no publisher-country inference, no defaulting to `eng`. Absent means `NULL`.
- Primary language is a lowercase 3-letter ISO 639-3 code. Additional languages follow the `genres_tags` convention — one `", "`-joined string column, not JSON (this repo has no JSON columns).
- ISBN stays optional; nothing here may make lookup a prerequisite for creating or editing a book.

**Ask First:**
- Any change to `suggest_classification`, `lcc_call_number`, `cutter_number`, or the call-number badge.
- Adding a batch-write endpoint, a vue-router, or a new top-level nav view.
- Bundling a full ISO 639-3 dataset.

**Never:**
- Do not touch `app/services/isbn_service.py` or `app/api/isbn.py` — capturing language from OpenLibrary is deferred work.
- Do not build a bulk-assign screen — also deferred.
- Do not re-key, re-classify, or migrate existing call numbers, and do not change key ordering.
- Do not touch the non-person author records or the duplicate book record.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Create with language | `POST /books` `{"title":"X","language":"PAN"}` | 201; stored and read back as `"pan"` | N/A |
| Invalid code | `language: "punjabi"` on create or update | 422 | Rejected — not exactly 3 ASCII letters |
| Empty string | `language: ""` on update | Stored as `NULL`, reads back `null` | N/A |
| Omitted | Book created without language | Both fields read as `null`; no chip on the card | N/A |
| Multi-language | `{"language":"eng","additional_languages":"san, hin"}` | Both round-trip; chip shows the primary label and `+2` | N/A |
| Filter | `GET /books?language=pan` | Only books whose primary language is `pan`; other filters unaffected | N/A |
| Filter miss | `GET /books?language=zzz` | Empty list, 200 | Not an error |

</frozen-after-approval>

## Code Map

- `app/models.py` -- indexed-optional-scalar pattern: `lcc_call_number`/`cutter_number` `:39-42`. Joined-string-list pattern: `genres_tags` (`:33`, `BookCreate:137`, `BookUpdate:154`, `BookRead:175`). `@field_validator` precedent: `AuthorInput:87-112`. Schemas at `:127-142`, `:144-162`, `:164-184`.
- `app/database.py:100-121` -- legacy upgrade block. Columns go inside `if book_table:` as `ALTER TABLE book ADD COLUMN <name> VARCHAR`, guarded against the `PRAGMA table_info(book)` set built at `:101-103`. Indexes are separate unconditional `CREATE INDEX IF NOT EXISTS ix_book_<column>` statements (`:116-121`); that name matches SQLAlchemy's default, which is how fresh and upgraded schemas converge.
- `app/services/book_service.py:182-202` -- `to_book_read()` hand-lists every field and is **the only `BookRead(...)` construction in the repo**; omit a field here and it reads `null` for every consumer. `create_book:205-219` and `update_book:288-316` are generic (`model_dump`/`setattr`) — no edit needed. `list_books:234-285`, discrete filters `:260-267`.
- `app/api/books.py:26-49` -- `list_books` query params, each a described `Query(...)`, forwarded at `:40-49`.
- `frontend/src/components/AddBookDialog.vue` -- `defaultForm():266-279`; text field `:112-117`; `genres_tags` comma field `:163-171`; free-entry `v-combobox` `:129-137`; `createPayload():381-401` with the `''`→`null` `textFields` list `:384-392`.
- `frontend/src/components/BookDetailDialog.vue` -- four edit sites: `emptyEditForm():416-431`, `startEdit()` hydration `:444-457`, `updatePayload()` textFields `:468-476`, template (edit inputs `:87-92`, display lines `:177-185`).
- `frontend/src/components/BookCard.vue` -- chip row `:25-70`; copy the shape of `callNumberDisplay` `:116-119` + its chip `:43-51`. No new prop needed — language rides on `book`.
- `frontend/src/utils/authors.js` + `authors.test.js` -- precedent for a pure helper plus a `node:test` file. Nothing runs it automatically; there is **no component test runner in the repo**.
- `frontend/src/services/api.js:17` -- `getBooks(params)` forwards arbitrary params; **no new API method needed**.
- `tests/test_authors_and_publishers.py:336-403` -- legacy-DB upgrade test; extend the assertions at `:371-385`, which check index names via `SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='book'`.
- `tests/test_classification.py:36-41` -- `_create_book(client, **overrides)` helper and the pure-then-API file structure to mirror. No `conftest.py` exists; each test file redeclares its in-memory engine, `session`, and `client` fixtures.

## Tasks & Acceptance

**Execution:**
- [x] `app/models.py` -- add `language: Optional[str] = Field(default=None, index=True)` and `additional_languages: Optional[str] = None` to `Book`; add both to `BookCreate`, `BookUpdate`, `BookRead`; add a `@field_validator` on the two input schemas that trims, lowercases, treats `""` as `None`, and rejects anything not exactly 3 ASCII letters -- makes language a first-class persisted attribute
- [x] `app/database.py` -- add the two `ALTER TABLE` guards plus `CREATE INDEX IF NOT EXISTS ix_book_language` inside the `if book_table:` block -- legacy databases upgrade to match a fresh schema
- [x] `app/services/book_service.py` -- add both fields to the `BookRead(...)` call in `to_book_read()`; add a `language` equality filter to `list_books` -- read data reaches every consumer and the catalog can be narrowed by language
- [x] `app/api/books.py` -- add a `language` query param to the `GET ""` route and forward it -- exposes the filter
- [x] `frontend/src/utils/languages.js` -- NEW: exported shortlist (`pan`, `eng`, `hin`, `san`, `urd`, `mul`) as `{code, label}` objects, plus pure `normalizeLanguage(input)` and `languageLabel(code)` helpers -- one source of truth for both forms and the card
- [x] `frontend/src/utils/languages.test.js` -- NEW: `node:test` coverage of both helpers, following `authors.test.js` -- the only executable frontend verification available
- [x] `frontend/src/components/AddBookDialog.vue` -- add a `v-combobox` for `language` (shortlist items, free entry allowed) and a comma-separated `additional_languages` text field; add both to `defaultForm()` and the `createPayload()` `textFields` list -- language enterable at creation
- [x] `frontend/src/components/BookDetailDialog.vue` -- mirror both fields across all four edit sites and add a read-only display line -- language editable after the fact
- [x] `frontend/src/components/BookCard.vue` -- add a `languageDisplay` computed and a `v-if`-guarded chip showing the primary language label, suffixed `+N` when additional languages are present -- language visible on the card
- [x] `tests/test_language.py` -- NEW: cover every row of the I/O matrix, mirroring `test_classification.py`'s pure-then-API structure -- locks in edge-case behavior
- [x] `tests/test_authors_and_publishers.py` -- extend the legacy-upgrade assertions at `:371-385` with the two new columns and `ix_book_language` -- proves the ALTER path actually runs

**Acceptance Criteria:**
- Given a legacy `book` table without the new columns, when `migrate_schema` runs, then both columns and `ix_book_language` exist and the API serves that database without error.
- Given books with mixed languages, when the books list is fetched with no `language` param, then the result is identical to before this story.
- Given a book edited to add a language, when the catalog is reloaded, then its card shows the language chip and `GET /books/{id}` reflects the stored code.
- Given any book in the catalog, when it is viewed, then its call number and badge are byte-identical to before this story.

## Design Notes

**Two columns, not JSON:** the repo has zero JSON columns; `genres_tags` establishes `", "`-joined `VARCHAR` as the house style for a string list. `language` is indexed (a filter and future grouping axis); `additional_languages` is display-only and is not.

**`additional_languages` ships now** because books in the collection are genuinely multilingual (`eng,san`, `mul`) — a single scalar is insufficient by design, and adding the column now avoids a second migration.

**`mul` is a real value**, the ISO 639-3 code for "multiple languages" — not a placeholder. How `mul` books shelve is deferred; storing it is not.

## Verification

**Commands:**
- `pytest tests/test_language.py -v` -- expected: all new tests pass
- `pytest` -- expected: full suite green, with `test_classification.py` and `test_catalog_and_isbn.py` unchanged in behavior
- `node --test frontend/src/utils/languages.test.js` -- expected: helper tests pass

**Manual checks (if no CLI):**
- Add a book with language Punjabi; confirm the chip appears on its card and the value survives a reload.
- Edit an existing book to set a primary language plus two additional ones; confirm the chip reads the primary label with `+2`.
- Confirm a book with no language shows no chip and no empty space where one would be.

## Suggested Review Order

**Validation — the "never guessed" rule made mechanical**

- Entry point: one normalizer defines what a language code is; empty means unknown, not English.
  [`models.py:144`](../../app/models.py#L144)

- Wired onto both input schemas, so create and update cannot diverge.
  [`models.py:176`](../../app/models.py#L176)

- Additional languages deliberately trim-only — free text per the `genres_tags` house style.
  [`models.py:133`](../../app/models.py#L133)

- Frontend mirror of the same rule; also accepts the object a combobox returns.
  [`languages.js:25`](../../frontend/src/utils/languages.js#L25)

**Schema & migration**

- Primary language indexed as a filter axis; additional languages are display-only.
  [`models.py:44`](../../app/models.py#L44)

- Legacy databases gain both columns; the index name matches SQLAlchemy's default.
  [`database.py:116`](../../app/database.py#L116)

- The single `BookRead` construction in the repo — omission here would null the field everywhere.
  [`book_service.py:202`](../../app/services/book_service.py#L202)

**Filtering**

- Normalize before guarding, so a whitespace-only filter is skipped rather than matching empty.
  [`book_service.py:272`](../../app/services/book_service.py#L272)

- Exposed alongside the existing genre/room/format filters; no frontend consumer yet.
  [`books.py:30`](../../app/api/books.py#L30)

**Display — pure functions, so the chip is testable**

- Extras deduped against the primary, so a repeated code cannot inflate the count.
  [`languages.js:63`](../../frontend/src/utils/languages.js#L63)

- Card chip: empty without a primary, which is what hides the chip entirely.
  [`languages.js:80`](../../frontend/src/utils/languages.js#L80)

- Detail view names the extras, and still reports them when no primary was set.
  [`languages.js:92`](../../frontend/src/utils/languages.js#L92)

- Component computeds are one-line delegations — no logic stranded in `.vue` files.
  [`BookCard.vue:131`](../../frontend/src/components/BookCard.vue#L131)

**Form binding**

- Combobox returns an object when picked; normalized to a code at payload time.
  [`AddBookDialog.vue:434`](../../frontend/src/components/AddBookDialog.vue#L434)

- Edit hydration resolves a stored code back to its shortlist item for display.
  [`BookDetailDialog.vue:494`](../../frontend/src/components/BookDetailDialog.vue#L494)

**Peripherals**

- Call-number invariance, guarded against a vacuous pass by asserting a real value exists first.
  [`test_language.py:210`](../../tests/test_language.py#L210)

- Legacy-upgrade test extended to prove the ALTER path actually ran.
  [`test_authors_and_publishers.py:389`](../../tests/test_authors_and_publishers.py#L389)

- Frontend tests now reachable by command rather than only by hand.
  [`package.json:9`](../../frontend/package.json#L9)
