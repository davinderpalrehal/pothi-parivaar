---
title: 'Domain-tuned LCC class map (story 2.3)'
type: 'feature'
created: '2026-08-31'
status: 'done'
review_loop_iteration: 0
baseline_commit: 'c445e582f444da56b4587c66a7fabdcf7b8f4244'
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `suggest_lcc_class` reads only `genres_tags`, which is empty for 37 of the 46 books in production, so 80% of the collection falls through to `DEFAULT_LCC_CLASS = "PN"`. The subject half of the shelf key carries almost no information, and the suggest dialog presents that guess as if it were a finding.

**Approach:** Let the class heuristic also read the title, prepend a domain-tuned keyword table reflecting what this library holds (Sikh religious works, Indic religion, juvenile/activity, workbooks, reference), and mark suggestions that matched nothing so the human is asked instead of handed `PN`.

## Boundaries & Constraints

**Always:**
- Classification stays **pure** — no DB session, no network, no `isbn_service` import. The hygiene guard at `tests/test_classification.py:242` keeps passing.
- Ordered checked-in tables, matched case-insensitively. `DOMAIN_LCC_MAP` matches on **word boundaries**; `GENRE_LCC_MAP` keeps plain substring matching and is consulted for `genres_tags` **only, never a title**.
- Precedence is strict: exhaust `genres_tags` through the domain table then the legacy table, and only then try `title` through the domain table. Domain entries always match before generic ones, and `genres_tags` is always checked before `title`.
- **Subject beats audience.** A juvenile book about a Sikh subject classifies `BL2017`, not `PZ`, so Sikh keywords precede juvenile keywords.
- Every existing assertion in `tests/test_classification.py` passes **unedited**. Achievable by adding `title` as an *optional* parameter and prepending rather than replacing.
- `PN` is still returned when nothing matches — flagged, not removed.

**Ask First:**
- Removing or renaming an existing `GENRE_LCC_MAP` entry.
- Matching proper names of specific works (`cinderella`, `aladdin`) — deliberately excluded as unbounded.
- Any change to `suggest_cutter`, `resolve_cutter_source`, or the persisted `Book` columns.

**Never:**
- Do not re-classify, re-key, or migrate existing books — all 46 are re-keyed in one later migration.
- Do not touch `app/services/isbn_service.py` or `app/api/isbn.py`, or add a second metadata source.
- Do not send the new marker on `PUT /books/{id}`; it describes the suggestion, not the book.
- Do not change key ordering or the badge format in `BookCard.vue` / `BookDetailDialog.vue`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Title-only signal | Title `"A Brief Introduction To The Sikh Faith"`, no `genres_tags` | `"BL2017"`, `class_source: "title"`, `class_matched_keyword: "sikh"` | N/A |
| Genres beat title | `genres_tags: "Hinduism, Rituals"`, title `"Sikh Concepts"` | `"BL1100"`, `class_source: "genres"` | N/A |
| Subject beats audience | Title `"Bed time stories 4 - Guru Tegh Bahadur ji"` | `"BL2017"` — not `PZ` | N/A |
| Legacy entry intact | `genres_tags: "History, Kids"` | `"D"` — unchanged from today | N/A |
| No signal | Title `"To Have And To Hold"`, no genres | `"PN"`, `class_source: "default"`, keyword `null` | Not an error |
| Dialog behavior | Fetched suggestion has `class_source: "default"` | Warning replaces the info hint; suppressed when the watcher skips the fetch for a book with stored values | N/A |

</frozen-after-approval>

## Code Map

- `app/services/classification_service.py` -- `DEFAULT_LCC_CLASS` `:23`; `GENRE_LCC_MAP` `:27-48` (insertion-ordered, "specific first" already its documented convention). `suggest_lcc_class(genres_tags)` `:51-65`, fallback returns at `:61` (empty) and `:65` (no match). `suggest_classification` `:167-183` is the **sole caller and already receives `title`**; builds `ClassificationSuggestion` at `:180-182`. Module docstring `:1-10` states the no-DB/no-network contract.
- `app/models.py:245-247` -- `ClassificationSuggestion`: plain non-table `SQLModel`, two required `str` fields, so new fields need defaults. Persisted `Book.lcc_call_number`/`cutter_number` (`:41-42`) and their `BookUpdate`/`BookRead` mirrors (`:201-202`, `:235-236`) are **out of scope**.
- `app/api/books.py:112-117` -- suggest route; returns the service object straight through, so a new model field propagates with **no route edit**.
- `frontend/src/components/ClassifySuggestDialog.vue` -- refs `:98-108`; `resetState()` `:122-130` (clear the new ref here); `fetchSuggestion` `:132-155` reads only the two fields at `:143-147`; info `v-alert` `:32-38` is the warning's insertion point; `confirm()` `:157-172` PUTs just two fields at `:162-165`; watcher `:186-204` skips the fetch at `:193-195` when values are already stored. `api.js:35-38` passes the raw response through — no change needed.
- `tests/test_classification.py` -- fixtures `:10-33` (no `conftest.py`; each file redeclares them), helpers `_create_book:36` / `_suggest:43`, pure-vs-API banners `:47` / `:83`. Assertions that must stay green unedited: `:52`, `:57`, `:63`, `:194`. `tests/test_language.py:210-242` reuses the suggestion body to PUT — harmless given defaults.
- `frontend/package.json:9` runs `node --test "src/utils/**/*.test.js"`; `frontend/src/utils/languages.js` + `languages.test.js` are the helper-plus-`node:test` precedent.

## Tasks & Acceptance

**Execution:**
- [x] `app/services/classification_service.py` -- add an ordered `DOMAIN_LCC_MAP` of `(keyword, class)` tuples covering Sikh `BL2017`, Hindu/Vedic `BL1100`, Buddhist `BQ`, juvenile/activity `PZ`/`PZ8`, education `LB`/`LB1573`/`QA`, games `GV1507`, reference `AG`/`AE`, comics `PN6790`, Indic literature `PK`, science `QA76`/`QP`/`QL`; change to `suggest_lcc_class(genres_tags, title=None)` searching domain then legacy table, over genres then title, returning the class plus the matched source and keyword -- gives the subject half of the key real information
- [x] `app/services/classification_service.py` -- pass `title` through in `suggest_classification`, populate the new fields, and update the module docstring for the title signal -- the assembler is the only caller
- [x] `app/models.py` -- add `class_source: str = "default"` and `class_matched_keyword: Optional[str] = None` to `ClassificationSuggestion` -- lets the dialog tell a match from a fallback
- [x] `frontend/src/components/ClassifySuggestDialog.vue` -- hold `class_source` in a ref, clear it in `resetState()`, and swap the info alert for a warning when it is `"default"` **and** a fetch actually ran; `confirm()` keeps sending only the two persisted fields -- surfaces "no signal" without changing what is saved
- [x] `tests/test_classification.py` -- add pure tests for every I/O matrix row (domain match, genres-before-title, subject-before-audience, legacy preservation, no-signal marker) plus an API test that the marker reaches the response and stays out of the confirmed `PUT` -- precedence is the part most likely to regress
- [x] `tests/test_classification.py` -- add a table-driven test over the **corpus fixture** in Design Notes: real titles from the collection paired with their expected class, including the seven that must stay `"default"` -- makes the coverage claim verifiable without production access

**Acceptance Criteria:**
- Given the assertions at `tests/test_classification.py:52,57,63,194`, when the suite runs, then they pass with **no edits to those lines**.
- Given a book already holding a call number, when catalog and detail views open, then its badge is byte-identical — nothing is re-classified.
- Given the checked-in corpus fixture below, when each title is classified with no `genres_tags`, then exactly the seven listed titles yield `class_source: "default"` and every other title yields its stated class.

## Spec Change Log

### 2026-08-31 — review iteration 1 (patched in place, human-approved)

**Triggering findings.** All three review layers independently found that bare
substring keywords misfire against free-text titles. Verified live: `art` matched
*Heartland*, *Smart Kids*, *Start Here*, *Particle Physics*, *A Part of the
Story*, *Wonders of the Earth*; `law` matched *Lawrence of Arabia*; and in the
domain table `color` matched *Colorado* and *Watercolor Painting*, `math` matched
*Mathura* and *Aftermath*, `plays` matched *Displays*, `trace` matched
*Traceability*. Separately, the implementation deviated from the frozen
"`genres_tags` is checked before `title`" rule by sweeping the domain table across
both fields before consulting the legacy table.

**Amendments.** Two frozen constraints were renegotiated with the human:
(1) `GENRE_LCC_MAP` is now genres-only and `DOMAIN_LCC_MAP` matches on word
boundaries, replacing the blanket "case-insensitive substring match" rule;
(2) the precedence bullet now states the field/table order explicitly rather than
leaving the cross-table case to inference.

**Known-bad state avoided.** Shipping a heuristic that assigns a confident,
non-default class — with `class_source: "title"` telling the librarian a real
keyword matched — to any book whose title merely contains *part*, *start*,
*heart*, *smart*, *earth*, *chart*, *math*, *color*, or *plays* inside an
unrelated word.

**KEEP.** These survived re-derivation and must not be undone: prepending the
domain table while leaving `GENRE_LCC_MAP` entries untouched, so the four
protected assertions at `tests/test_classification.py:52,57,63,194` still pass
unedited; `title` as an *optional* second parameter; `LccClassMatch` as a `str`
subclass, which is what makes those assertions keep working; and the corpus
fixture as the verifiable stand-in for production access.

## Design Notes

**Prepend, don't replace** — the domain table is searched first, `GENRE_LCC_MAP` is kept intact as the tail, and `title` is optional. That is why no existing assertion changes; this was verified against the real expectations before the spec was written. Generic `history` stays `D`; Sikh history reaches `BL2017` because `sikh` precedes `history` in search order, not because `history` was remapped. Ordering *is* the design: specific before generic, subject before audience.

**Measured on production** (46-book read-only snapshot, prod unmodified): fallback drops 37/46 → 7/46; distinct classes rise 3 → 13 (`BL2017` 18, `PZ` 5, `AG` 4, `BL1100` 3).

**The table** (order matters; this exact list produced the numbers above):

```
BL2017: gurbani, sikhism, sikh, guru, gurmukh, guramukha, "bhai ", sahibzada, bara maha, khalsa
BL1100: hindu, vedic, veda        BQ: buddha, buddhis
PZ: colouring, coloring, color, trace, sticker, storybook, bed time, bedtime,
    activity book, juvenile, children     PZ8: fairy
QA: maths, math    LB: workbook    LB1573: spelling    GV1507: crossword
AG: world records, "wonders of the wor"   AE: encyclopedia
PN6790: comic   PK: kalidasa, panjabi, punjabi, plays
QA76: language models, computer    QP: human body    QL: ocean
```

**Corpus fixture** for the table-driven test — real titles, classified with no `genres_tags`:

| Title | Expected |
|---|---|
| A Brief Introduction To The Sikh Faith | `BL2017` |
| Bed time stories 4 - Guru Tegh Bahadur ji | `BL2017` (subject beats `bed time`) |
| Vedic Eternal Truth Part Two | `BL1100` |
| Gautam Buddha a Biography | `BQ` (beats legacy `biography` → `CT`) |
| COLOURING BOOK FOR DORA | `PZ` |
| Trace And Color Objects | `PZ` |
| Power Maths Reception Journal a - 2021 Edition | `QA` |
| Time for Spelling | `LB1573` |
| SUPER LARGE PRINT CROSSWORD Book 7 | `GV1507` |
| Guinness World Records 2002 | `AG` |
| Great Plays of Kalidasa | `PK` |
| Hands-On Large Language Models | `QA76` |
| THE HUMAN BODY | `QP` |
| Ocean Creatures with over 70 reusable stickers! | `PZ` (`sticker` precedes `ocean`) |

Must stay `class_source: "default"` → `PN`: *My Baby Book: The First Five Years*, *I Love You This Much*, *At The Feet Of The Master*, *To Have And To Hold*, *TERCENTENARY CELEBRATIONS*, *Cinderella*, *Aladdin and the Magic Lamp*. These are genuinely ambiguous and meant to be flagged.

## Verification

**Commands:**
- `pytest tests/test_classification.py -v` -- expected: all pass, including the four pre-existing assertions unedited
- `pytest` -- expected: full suite green; `test_language.py` and `test_authors_and_publishers.py` unchanged in behavior
- `cd frontend && npm run build` -- expected: builds clean

**Manual checks (if no CLI):**
- Suggest on a Sikh-subject title with no genres: class is `BL2017`, normal review hint shows.
- Suggest on an unmatched title: warning appears, class field still editable.
- Open on a book with a stored call number: no warning, stored values shown.

## Suggested Review Order

**The heuristic — start here**

- Entry point: the domain table is prepended, never replacing the legacy one.
  [`classification_service.py:70`](../../app/services/classification_service.py#L70)

- Precedence made explicit: genres exhausted through both tables before title.
  [`classification_service.py:210`](../../app/services/classification_service.py#L210)

- The legacy table is genres-only; bare substrings misfire badly on free text.
  [`classification_service.py:243`](../../app/services/classification_service.py#L243)

- Word boundaries plus one absorbed inflection, compiled once at import.
  [`classification_service.py:148`](../../app/services/classification_service.py#L148)

**Provenance — how a match is told from a fallback**

- A `str` subclass, which is why every pre-existing assertion still passes.
  [`classification_service.py:166`](../../app/services/classification_service.py#L166)

- Copy and pickle support; without it the subclass raised on `copy.copy`.
  [`classification_service.py:196`](../../app/services/classification_service.py#L196)

- Typed as a Literal, so a service-side typo cannot reach the dialog.
  [`models.py:251`](../../app/models.py#L251)

**UI — the only part that changes what a human does**

- Predicate extracted to a helper so it is testable without a component runner.
  [`classification.js:19`](../../frontend/src/utils/classification.js#L19)

- Warning replaces the review hint only when a fetch actually returned default.
  [`ClassifySuggestDialog.vue:35`](../../frontend/src/components/ClassifySuggestDialog.vue#L35)

**Peripherals — the guards that pin all of the above**

- Negative guard: legacy keywords must never reach a title.
  [`test_classification.py:137`](../../tests/test_classification.py#L137)

- Negative guard: domain keywords must not match inside unrelated words.
  [`test_classification.py:160`](../../tests/test_classification.py#L160)

- Cross-table precedence, the combination no earlier test observed.
  [`test_classification.py:245`](../../tests/test_classification.py#L245)

- Real collection titles with their expected class and matched keyword.
  [`test_classification.py:287`](../../tests/test_classification.py#L287)

- Persistence guard, rewritten to actually send the marker in the PUT body.
  [`test_classification.py:514`](../../tests/test_classification.py#L514)

