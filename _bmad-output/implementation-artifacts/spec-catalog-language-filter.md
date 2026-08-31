---
title: 'Catalog language filter'
type: 'feature'
created: '2026-08-31'
status: 'done' # draft | ready-for-dev | in-progress | in-review | done
review_loop_iteration: 0
baseline_commit: '9e8ee0529f6fd799d97c0cfea30d5ab9a35c17ed'
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Story 2.2 shipped `GET /books?language=` with no frontend consumer — `App.vue`'s filter bar was never touched — so the epic's stated motivation, grouping by language, is unreachable from the catalog. Most books also have no language yet and there is no way to see which.

**Approach:** Add an endpoint reporting the distinct primary languages actually held plus how many books have none, and drive a new catalog filter control from it, including a "No language set" choice backed by a new `missing_language` param.

## Boundaries & Constraints

**Always:**
- `GET /books/languages` must be declared **before** `GET /{book_id}` in `app/api/books.py`. Declared after, FastAPI resolves `languages` as a book id and 422s.
- The dropdown is fed by the endpoint, never by `LANGUAGE_OPTIONS` — that stays the *entry* form's suggestions. Any well-formed 3-letter code held in the catalog must be filterable.
- "Missing" means `Book.language IS NULL` **or** `''` — do not rely on the write validator only ever storing `NULL`.
- Filters keep AND semantics; `missing_language` defaults false, so an unparametrized `GET /books` is byte-identical to today.
- Option-list and param construction live in **pure helpers** in `languages.js` with `node:test` coverage — no logic stranded in `App.vue`. That suite is the repo's only executable frontend check.
- Language is never guessed or written here; this story reads and filters only.

**Ask First:**
- Changing an existing `LANGUAGE_OPTIONS` entry or the entry-form combobox.
- Adding a vue-router, a new top-level nav view, or a batch-write endpoint.
- Any change to `suggest_classification`, the call-number columns, or the card badges.

**Never:**
- Do not build the bulk-assign dialog — deferred, though this lands the `missing_language` param it needs.
- Do not touch `isbn_service.py` / `api/isbn.py`, or expose language via `api/hermes.py` (separate deferred entry).
- Do not re-key, re-classify, or migrate books. No new columns, so no `database.py` change.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Summary | 18 `pan`, 4 `eng`, 1 `tam`, 34 unset | `{"languages":[{"code":"pan","book_count":18},{"code":"eng","book_count":4},{"code":"tam","book_count":1}],"missing_count":34}` — unknown codes included | N/A |
| Route not shadowed | `GET /books/languages` | 200 summary, never a 422 from `/{book_id}` | N/A |
| Empty catalog | no books | `{"languages":[],"missing_count":0}`, 200 | Not an error |
| Missing filter | `?missing_language=true` | only books whose primary language is `NULL` or `''` | N/A |
| Both params | `?language=pan&missing_language=true` | empty list, 200 — plain AND, no special-casing | Not an error |
| Default off | `GET /books`, no new param | identical to before this story | N/A |
| Options built | `{languages:[{code:'pan',book_count:18}],missing_count:3}` | `[{title:'Punjabi (18)',value:'pan'},{title:'No language set (3)',value:'__none__'}]`; missing entry omitted when count is 0 | N/A |
| Param mapping | `'__none__'` / `'pan'` / `null` | `{missing_language:true}` / `{language:'pan'}` / `{}` | N/A |

</frozen-after-approval>

## Code Map

- `app/api/books.py` -- `list_books` `:24-52`; filters are described `Query(...)` at `:26-30`, forwarded `:42-49` (`language` already wired `:30`/`:47`). **`@router.get("/{book_id}")` is at `:65`** — the new route goes above it.
- `app/services/book_service.py` -- `list_books:236-292`, discrete filters `:265-274`, existing `language` filter `:272-274` (normalizes before guarding). `to_book_read:182-204` already carries both language fields.
- `app/models.py` -- `ClassificationSuggestion:245`, the non-table response-object precedent; put the new models near it. `normalize_language_code:144` is write-side only.
- `app/services/location_service.py:93` + `app/api/locations.py:42-45` -- aggregate-endpoint precedent: service computes, thin route returns. Untyped `dict` there; typed here.
- `frontend/src/App.vue` -- bar `:75-150` (`v-row:77`; search `:78-88`, tag `:90-100`, format `:102-112`, status `:114-124`, room `:126-136`, refresh `:138-148`); refs `:321-324`, option arrays `:325-336`, `fetchBooks` params `:348-357`, imports `:306-312` (no util import yet), `handleBookSaved:407` and `onMounted:426` are the two refresh hooks.
- `frontend/src/utils/languages.js` -- `LANGUAGE_OPTIONS:4` (leave alone), `normalizeLanguage:26`, `languageLabel:41` (uppercases unknown codes — reuse for titles). Tests run via `frontend/package.json:9`.
- `frontend/src/services/api.js:17-19` -- `getBooks(params)` forwards arbitrary params; add the getter alongside.
- `tests/test_language.py` -- fixtures `:10-33` (no `conftest.py`), `_create_book:36`, pure/API banners `:43`/`:81`, filter tests `:136-208` to mirror.

## Tasks & Acceptance

**Execution:**
- [x] `app/models.py` -- add non-table `LanguageSummaryRead` (`code: str`, `book_count: int`) and `CatalogLanguagesRead` (`languages`, `missing_count`) -- typed contract, unlike `locations_summary`
- [x] `app/services/book_service.py` -- add `catalog_languages(session)` returning held codes with counts (`book_count` desc, then `code` asc) plus the null-or-blank count; add `missing_language: bool = False` to `list_books` -- one grouped query feeds the dropdown, the flag makes the gap reachable
- [x] `app/api/books.py` -- add `@router.get("/languages")` **above** `/{book_id}`, and a `missing_language` `Query(False, ...)` forwarded to the service
- [x] `frontend/src/services/api.js` -- add `getCatalogLanguages()`
- [x] `frontend/src/utils/languages.js` -- add `MISSING_LANGUAGE_VALUE = '__none__'`, pure `languageFilterOptions(summary)` (titles via `languageLabel`, counts suffixed, missing entry appended last and only when `missing_count > 0`) and pure `languageFilterParams(value)`
- [x] `frontend/src/utils/languages.test.js` -- cover both helpers against every matrix row naming them, plus the unknown-code label fallback
- [x] `frontend/src/App.vue` -- restructure into two rows (row 1 search `md=11` + refresh `md=1`; row 2 tag/format/status/room/language at `md=2`), add a `languageFilter` ref and `v-select` fed by `languageFilterOptions`, load the summary on mount and again in `handleBookSaved` so counts cannot go stale, and merge `languageFilterParams` into `fetchBooks`
- [x] `tests/test_language.py` -- API tests for the endpoint (populated, empty, unknown code held, not shadowed) and `missing_language` (matches unset, empty when combined with `language=`, absent param unchanged)

**Acceptance Criteria:**
- Given the catalog with no filters, when it loads, then the books shown match the pre-story set and the language control is populated from the endpoint.
- Given a language is picked then cleared, when each fetch runs, then the request carries exactly one of `language`, `missing_language`, or neither — never both.
- Given a book's language is edited in the detail dialog, when the catalog refreshes, then the dropdown counts reflect it without a page reload.
- Given the `xs`, `sm`, and `md` breakpoints, when the bar renders, then no control overflows its row and refresh stays beside search.

## Design Notes

**Endpoint, not the shortlist:** `LANGUAGE_OPTIONS` is six seed codes for entry, but `normalizeLanguage` accepts any well-formed code, so the catalog can hold `tam` or `guj` — a shortlist-driven filter would hide them silently, and could offer languages with zero results.

**The missing entry goes last**, not sorted into the count order: it is a different kind of thing from a language, and with most of the collection unset it would otherwise dominate the top. `'__none__'` cannot collide — every real value is exactly three ASCII letters, enforced both sides.

**AND needs no special-casing:** `language = 'pan' AND language IS NULL` is unsatisfiable, so both params together return empty on their own. Do not add a validator rejecting the pair.

## Verification

**Commands:**
- `pytest tests/test_language.py -v` -- expected: all pass, existing tests unedited
- `pytest` -- expected: full suite green; `test_classification.py` and `test_catalog_and_isbn.py` unchanged in behavior
- `cd frontend && npm test` -- expected: `languages.test.js` passes including the new cases
- `cd frontend && npm run build` -- expected: builds clean

**Manual checks (if no CLI):**
- Pick a language: the grid narrows and the option's count matches the card count. Clear it: the full catalog returns.
- Pick "No language set": only books with no language chip appear.
- Narrow to phone width: controls stack without overflow.

## Suggested Review Order

**Route declaration — start here, this is the whole trap**

- Entry point: `/languages` declared above `/{book_id}`, or FastAPI 422s on it.
  [`books.py:70`](../../app/api/books.py#L70)

- The guard that pins it; all five endpoint tests fail if the route moves down.
  [`test_language.py:328`](../../tests/test_language.py#L328)

**Deriving the option list from the data**

- Grouped read, counts merged by normalized code so one option never appears twice.
  [`book_service.py:306`](../../app/services/book_service.py#L306)

- Typed contract, unlike the untyped dict the locations summary returns.
  [`models.py:262`](../../app/models.py#L262)

**Reaching the books that have no language**

- NULL or blank, deliberately not trusting the write validator's NULL-only guarantee.
  [`book_service.py:282`](../../app/services/book_service.py#L282)

- Defaults false, which is what keeps an unparametrized list byte-identical.
  [`books.py:32`](../../app/api/books.py#L32)

- Proves the blank half of that rule by inserting a row the API cannot create.
  [`test_language.py:363`](../../tests/test_language.py#L363)

**Pure helpers — the only frontend logic that is executable**

- Missing entry appended last, and omitted entirely when nothing is unset.
  [`languages.js:115`](../../frontend/src/utils/languages.js#L115)

- Maps a selection to exactly one query key, never both.
  [`languages.js:139`](../../frontend/src/utils/languages.js#L139)

- Sentinel cannot collide: every real value is three ASCII letters.
  [`languages.js:105`](../../frontend/src/utils/languages.js#L105)

**Wiring — where the component delegates rather than decides**

- One line of param assembly; all the logic sits in the tested helper.
  [`App.vue:377`](../../frontend/src/App.vue#L377)

- Review-added: drops a selection whose option no longer exists after a save.
  [`App.vue:437`](../../frontend/src/App.vue#L437)

- Rebuilt on mount and after every add, edit, and delete, so counts cannot go stale.
  [`App.vue:428`](../../frontend/src/App.vue#L428)

**Peripherals**

- The new control; row two of the restructured two-row bar.
  [`App.vue:153`](../../frontend/src/App.vue#L153)

- The single new API call.
  [`api.js:35`](../../frontend/src/services/api.js#L35)

- Round-trip guard: every option the endpoint offers maps back to a real filter.
  [`languages.test.js:234`](../../frontend/src/utils/languages.test.js#L234)
