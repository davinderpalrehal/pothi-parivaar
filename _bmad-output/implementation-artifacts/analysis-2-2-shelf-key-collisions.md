# Analysis: shelf-key collisions and language grouping (epic 2)

Input for story 2.2. Evidence gathered 2026-08-31 against the **production**
database (read-only snapshot pulled over Tailscale SSH from
`hermes@100.79.172.22:/home/hermes/apps/pothi-parivaar/data/pothi.db`).
Production was not modified.

Collection at time of analysis: **46 books, 34 authors, 0 publishers.**

## 1. Measured collision rate

All 46 books have a stored `lcc_call_number`. 25 sit on a duplicate stored key,
but some stored values are stale or hand-entered and are **not** what the current
code produces — the 8-book `PN A28` cluster recomputes to `I52`, `P28`, `G27`,
`E52`, `T27`, `B42`. Re-running today's `suggest_classification` over all 46:

> **31 distinct keys. 23 of 46 books (50%) collide, across 8 keys.**

## 2. Root causes

### 2a. The subject class carries no information — 93% of the library is `PN`

| LCC class | books | | `genres_tags` | books |
|---|---|---|---|---|
| `PN` | 43 | | *(empty)* | **37** |
| `CT` | 2 | | populated | 9 |
| `D`  | 1 | | | |

`suggest_lcc_class` returns `DEFAULT_LCC_CLASS = "PN"` whenever `genres_tags` is
empty, and it is empty for 80% of books: OpenLibrary returns subjects for only
some ISBNs, and the manual add path never asks. The first half of every shelf key
is effectively a constant.

### 2b. The Cutter collapses exactly the names this library is full of

`CUTTER_DIGIT_TABLE` maps 26 letters into 8 buckets, puts all six vowels in
bucket `2`, dedupes immediate repeats, and emits 1 letter + 2 digits.

- `Singh` -> `S26` and `Sing` -> `S26` (5 books; Singh is the modal surname here)
- `Buddha` -> `B23` and `Baby` -> `B23` (unrelated authors, same slot)
- `Pai` x3, `Watson` x3, `Greetings` x3 (same author, no work-level distinction)

### 2c. No uniqueness mechanism exists

`suggest_classification` is pure and never consults the shelflist, so nothing
*can* prevent a collision. Real LCC practice appends a work mark and date
(`PN6110.C4 S26b 1985`) and treats the shelflist as the authority.

### 2d. No `language` field anywhere

Not on `Book`, and `lookup_isbn` does not capture it — it calls OpenLibrary
`jscmd=data`, which omits language. Language cannot be inferred from script:
every title in the collection is Latin, including romanized Punjabi
(`Bhāī sāhiba Bhāī Wīra Siṅgha jī dā guramukha jīwana`).

## 3. Prototype result

3-digit positional Cutter (no vowel collapse, no dedupe, diacritics folded via
NFKD) + work mark from the first non-article title word + publication year,
measured on the same 46 books:

| Key shape | Colliding books |
|---|---|
| current (`S26`) | 23 / 46 — **50%** |
| 3-digit Cutter | 20 / 46 — 43% |
| + work mark | 7 / 46 — 15% |
| + work mark + year | 4 / 46 — **9%** |

The 4 survivors are real-world cases, not algorithm failures:

- ids **9 & 35** — genuinely duplicated record, same ISBN `9788122314755`
- ids **28 & 30** — *ELUCIDATION [Part-V]* vs *ELUCAIDATION [Part-III]*, real
  series volumes needing a part designation

Both are resolved by a shelflist uniqueness check rather than more entropy.

## 4. Language backfill coverage — measured, not assumed

OpenLibrary `jscmd=details` **does** return language
(`languages: [{key: "/languages/pan"}]`) and subjects, with no API key. Tested
against all 30 ISBNs in production:

| Result | books |
|---|---|
| Language returned (`eng`, `pan`, `mul`, `eng,san`) | **12** |
| ISBN present, no OpenLibrary record | 17 |
| Subjects only, no language | 1 |
| No ISBN at all | 16 |
| **Total** | **46** |

**Automatic language coverage tops out at 26%.** Google Books is not a fallback
without provisioning: the unauthenticated endpoint currently returns
`429 Quota exceeded` on a shared IP quota.

Two shape constraints this surfaced:

- **Multi-language books exist.** Book 9/35 -> `eng,san`; book 7 -> `mul`. The
  model needs a *primary* language for shelving plus optional additional
  languages, not a single scalar.
- **A series can split.** *Bed time stories 1* -> `pan` but *Bed time stories 4*
  -> `mul`; a strict language-first key separates volumes that belong together.

## 5. Data-quality issues found (separate from the algorithm)

**8 of 34 author records are not people** — publishers and honorifics feeding
garbage into the Cutter:

| id | first_name | last_name |
|---|---|---|
| 3  | Unknown | Author |
| 17 | Sikh | (Regd |
| 19 | The | House |
| 24 | unknown | Author |
| 27 | T. | M.A. |
| 31 | Autumn | publishing |
| 32 | Alligator | LTD |
| 33 | International | Greetings |

**One duplicate book record**: ISBN `9788122314755` exists as ids 9 and 35.

## 6. Decisions taken

| # | Decision | Choice |
|---|---|---|
| 1 | Key ordering | **Language -> Subject -> Author** (language is the outermost shelf block) |
| 2 | Uniqueness | **Widen key + shelflist check** at assign time; extend work mark (`b` -> `b2`) until free |
| 3 | Subject coverage | **Domain-tuned class map** (title keywords, not just `genres_tags`) **+ second metadata source** |
| 4 | Language fill for the 34 misses | **Bulk-assign screen**; nothing guessed |
| 5 | Migration | **Re-key all 46 in one migration** once language and subjects are filled |

### Target key shape

```
ENG · PZ · W287m        My Baby Book: The First Five Years
PAN · PZ · S464b        Bed time stories 4 - Guru Tegh Bahadur ji
PAN · CT · S464b2       Bhāī sāhiba Bhāī Wīra Siṅgha jī dā guramukha jīwana
      ↑     ↑    ↑
      |     |    └─ work mark (first non-article title word) + shelflist suffix
      |     └────── 3-digit positional Cutter, diacritics folded
      └──────────── domain-tuned LCC class
```

Stored as **components, not one opaque string**, so the catalog can group and
filter on each: `language` (ISO 639-3) + `lcc_call_number` + widened
`cutter_number`, with a uniqueness constraint across the three.

## 7. Implications for implementation

- `suggest_classification` stops being pure — it takes a session and consults the
  shelflist. The existing purity tests in `tests/test_classification.py` change.
- `Book` gains `language` (primary, ISO 639-3) and needs an additive migration in
  `app/database.py`, matching how `lcc_call_number`/`cutter_number` were added.
- `lookup_isbn` moves from `jscmd=data` to `jscmd=details` (or calls both) to
  capture `languages` and richer `subjects`.
- Google Books as second source **requires an API key** to be dependable.
- The 8 non-person author records and the duplicate book should be cleaned before
  the re-key migration, or they will produce confidently-wrong keys.

## 8. Open items not yet decided

- Vocabulary shown in the bulk-assign UI (ISO 639-3 codes vs friendly names) and
  which languages appear as quick buttons.
- How `mul` / multi-language books shelve — primary language only, or a dedicated
  block.
- Whether series volumes get an explicit part designation in the key.
