## Deferred from: code review of spec-reader-profiles-and-progress.md (2026-08-20)

- Catalog `GET /books` default `limit=100` (`app/api/books.py:26`) — pre-existing list default; a 1,000-book library is silently truncated on the catalog grid. Not introduced by the reader-profile change.

- source_spec: `/Users/davinderpalrehal/Projects/pothi-parivaar/_bmad-output/implementation-artifacts/spec-fr-7-8-13-locations-formats-recommend.md`
  summary: FR-8 Digital format association — optional file path / cloud link note and per-format catalog icons.
  evidence: Split from a combined FR-7/8/13 spec that exceeded the 1600-token budget; independently shippable on the Book form without the location registry.

- source_spec: `/Users/davinderpalrehal/Projects/pothi-parivaar/_bmad-output/implementation-artifacts/spec-fr-7-8-13-locations-formats-recommend.md`
  summary: FR-13 Hermes recommendation helper — GET /api/v1/books/recommend with topic, age_appropriate, and exclude_read_by.
  evidence: Split from a combined FR-7/8/13 spec that exceeded the 1600-token budget; independently shippable agent API with no UI dependency on locations.

- source_spec: `/Users/davinderpalrehal/Projects/pothi-parivaar/_bmad-output/implementation-artifacts/spec-fr-7-8-13-locations-formats-recommend.md`
  summary: Catalog room filter is exact-match, so a summary chip labeled Office can hide books stored as office.
  evidence: Frozen spec kept GET /books?room= exact equality; case-insensitive occupancy merge is registry-only.

- source_spec: `/Users/davinderpalrehal/Projects/pothi-parivaar/_bmad-output/implementation-artifacts/spec-fr-7-8-13-locations-formats-recommend.md`
  summary: Occupancy Unassigned map chip cannot list books with a null room via the catalog room filter.
  evidence: Spec required filter-room emit unchanged; App.vue passes the emitted string as exact location_room.

- source_spec: `/Users/davinderpalrehal/Projects/pothi-parivaar/_bmad-output/implementation-artifacts/spec-fr-7-8-13-locations-formats-recommend.md`
  summary: No automated frontend tests for location combobox cascade (empty unit/shelf still selectable).
  evidence: Repo has no Vue test runner; coverage is API-only in tests/test_locations.py.

- source_spec: `/Users/davinderpalrehal/Projects/pothi-parivaar/_bmad-output/implementation-artifacts/spec-1-2-author-add-edit-ui.md`
  summary: Optional publisher name field on Add Book and Book Detail.
  evidence: Split from the 1.2 UI spec over the token budget; independently shippable after structured authors save; CAP-8 write UI.

- source_spec: `/Users/davinderpalrehal/Projects/pothi-parivaar/_bmad-output/implementation-artifacts/spec-1-2-author-add-edit-ui.md`
  summary: Dedicated mononym control (checkbox or “single name” switch) on author rows.
  evidence: Split from the 1.2 UI spec over the token budget; last-name field posting a single space is enough for Cher/Plato.

- source_spec: `/Users/davinderpalrehal/Projects/pothi-parivaar/_bmad-output/implementation-artifacts/spec-1-2-author-add-edit-ui.md`
  summary: No Vue/Playwright tests that mount Add Book or Book Detail and spy createBook/updateBook.
  evidence: Repo has no Vue test runner; matrix coverage is frontend/src/utils/authors.test.js plus pytest API tests.

## Deferred from: code review of spec-2-1-lcc-cutter-shelf-key.md (2026-08-26)

- source_spec: `/Users/davinderpalrehal/Projects/pothi-parivaar/_bmad-output/implementation-artifacts/spec-2-1-lcc-cutter-shelf-key.md`
  summary: Title-based Cutter source doesn't strip leading articles ("A"/"An"/"The") before computing the code.
  evidence: Zero-author books Cutter off the raw title (e.g. "A Brief History of Time" Cutters from "A"), diverging from conventional Cutter-table practice; spec explicitly allows a non-authoritative heuristic, so this is a future refinement, not a defect.

- source_spec: `/Users/davinderpalrehal/Projects/pothi-parivaar/_bmad-output/implementation-artifacts/spec-2-1-lcc-cutter-shelf-key.md`
  summary: suggest_cutter strips non-ASCII/diacritic characters (e.g. "García" -> "Garca") instead of transliterating, with no test coverage for accented, hyphenated, or apostrophe'd names.
  evidence: A family/small-library catalog plausibly holds non-English author names; spec scoped the algorithm as heuristic-only, so this is a robustness improvement, not a spec violation.

- source_spec: `/Users/davinderpalrehal/Projects/pothi-parivaar/_bmad-output/implementation-artifacts/spec-2-1-lcc-cutter-shelf-key.md`
  summary: No collision avoidance when two different books resolve to the same LCC class + Cutter code.
  evidence: Real Cutter tables exist to keep works uniquely ordered within a class; this heuristic MVP has no uniqueness check. Not required by the story's AC or the user's "smaller mapping table" scope decision.

- source_spec: `/Users/davinderpalrehal/Projects/pothi-parivaar/_bmad-output/implementation-artifacts/spec-2-1-lcc-cutter-shelf-key.md`
  summary: ClassifySuggestDialog's suggestion fetch has no request-ordering guard, so a slow response could overwrite a newer one if the dialog is reopened quickly for a different book.
  evidence: Low likelihood in single-family/single-user usage; worth hardening if the app ever supports concurrent multi-user editing.

- Frontend has no test runner or framework configured anywhere in the repo (only `frontend/src/utils/authors.test.js` exists, no `test` script in `frontend/package.json`), so the new `ClassifySuggestDialog.vue` and the call-number badges have no executable frontend verification. Pre-existing project-wide gap, not introduced by this story — surfaced incidentally while reviewing the new UI.

## Deferred from: story 2.2 intent split (2026-08-31)

- source_spec: none
  summary: Domain-tuned LCC class map keyed off title keywords plus a second metadata source, replacing the DEFAULT_LCC_CLASS="PN" fallback.
  evidence: Split from the 2.2 intent as an independently shippable goal; 43/46 books classify as PN because genres_tags is empty for 37 of them, but fixing subject coverage needs no schema change and ships without the language work.

- source_spec: none
  summary: Collision-proof Cutter — 3-digit positional Cutter with diacritics folded, title work mark plus publication year, and a shelflist uniqueness check at assign time (suggest_classification takes a session; work mark extends b -> b2).
  evidence: Split from the 2.2 intent as an independently shippable goal; measured to take collisions from 50% to 9% on its own, independent of language capture. Rewrites the purity tests in tests/test_classification.py.

- source_spec: none
  summary: Language-first key ordering (LANG - CLASS - CUTTER) stored as components with a uniqueness constraint, badge display update, and a one-shot migration re-keying every existing book.
  evidence: Split from the 2.2 intent; depends on language capture, the class map, and the new Cutter all landing first. Holding it until then avoids re-keying the collection twice.

- source_spec: none
  summary: Catalog data cleanup — 8 author records that are publishers/honorifics rather than people (ids 3, 17, 19, 24, 27, 31, 32, 33) and the duplicate book record for ISBN 9788122314755 (ids 9 and 35).
  evidence: Split from the 2.2 intent; independent of the algorithm work but must land before any re-key migration, or it bakes confidently-wrong keys into the collection.

- source_spec: `/Users/davinderpalrehal/Projects/pothi-parivaar/_bmad-output/implementation-artifacts/spec-2-2-book-language-capture.md`
  summary: Fullscreen bulk language-assign dialog on the catalog, loading books with no language via a new missing_language filter and saving one PUT /books/{id} per changed row with per-row error reporting.
  evidence: Split from the 2.2 spec over the token budget; independently shippable once the language field exists, since books can already be given a language one at a time through the edit dialog. Needs a missing_language query param added to GET /books alongside the language param this story ships.

- source_spec: `/Users/davinderpalrehal/Projects/pothi-parivaar/_bmad-output/implementation-artifacts/spec-2-2-book-language-capture.md`
  summary: Capture language from OpenLibrary via an additive best-effort jscmd=details fetch, expose it on IsbnLookupRead, and pre-fill it on the add-book form.
  evidence: Split from the 2.2 spec over the token budget; measured to cover only ~26% of the collection so it is an accelerator over manual entry, not the main path. Must stay additive — the details view nests under ["details"] and returns subjects as bare strings, so repointing the existing jscmd=data mapping would silently null genres_tags. Requires reworking the URL-blind mock in tests/test_catalog_and_isbn.py:228-236 to a two-response side_effect.

## Deferred from: code review of spec-2-2-book-language-capture.md (2026-08-31)

- source_spec: `/Users/davinderpalrehal/Projects/pothi-parivaar/_bmad-output/implementation-artifacts/spec-2-2-book-language-capture.md`
  summary: No catalog filter control for language — GET /books?language= ships with no frontend consumer, since App.vue's filter bar and param assembly were left untouched.
  evidence: Deliberately scoped out of 2.2 (the story's task list omits App.vue), but grouping and filtering by language is the stated motivation for the epic, so the control is real outstanding work. Would also want an endpoint returning the catalog's distinct languages rather than hardcoding the shortlist a second time.

- source_spec: `/Users/davinderpalrehal/Projects/pothi-parivaar/_bmad-output/implementation-artifacts/spec-2-2-book-language-capture.md`
  summary: Language is invisible to the Hermes agent surfaces — app/api/hermes.py hand-builds its response dicts without it, and the free-text q search in list_books does not match on language.
  evidence: Hermes cannot answer "find me a Punjabi book" even though the column now exists; get_library_status also has no per-language counts. Out of scope for 2.2, which never touched the Hermes layer, but the capability gap is real now that the data is being captured.

## Deferred from: LCC class map intent split (2026-08-31)

- source_spec: none
  summary: Second metadata source for subject/genre coverage — provision a Google Books API key (or equivalent) and merge its subjects into the classification signal alongside OpenLibrary.
  evidence: Split from the class-map intent as an independently shippable goal; needs API-key provisioning (the unauthenticated endpoint returns 429 on shared-IP quota) and edits app/services/isbn_service.py, which both the deferred jscmd=details language capture and epic-1 story 1-3 isbn-author-name-split also touch. The title-keyword class map ships without it and covers the 37/46 books that have no genres_tags at all.

## Deferred from: code review of spec-2-3-lcc-class-map.md (2026-08-31)

- source_spec: `/Users/davinderpalrehal/Projects/pothi-parivaar/_bmad-output/implementation-artifacts/spec-2-3-lcc-class-map.md`
  summary: Domain table has no core Sikh vocabulary beyond "guru"/"sikh" — no nanak, granth, ardas, japji, singh, kaur, or waheguru.
  evidence: Verified against the shipped code: "Nanak Dukhiya Sab Sansar" and "Ardas and Japji" both fall through to a flagged PN. The story deliberately chose "safe generics only" and accepted 7 flagged books, but for a Sikh-majority collection these are domain terms rather than the proper-name matching the spec's Ask First bars. "TERCENTENARY CELEBRATIONS", one of the 7, is very likely a Khalsa tercentenary work.

- source_spec: `/Users/davinderpalrehal/Projects/pothi-parivaar/_bmad-output/implementation-artifacts/spec-2-3-lcc-class-map.md`
  summary: Book.language is captured but unused as a classification signal, while "punjabi"/"panjabi" sit in the subject table doing language work.
  evidence: Story 2.2 shipped an indexed ISO 639-3 language column and suggest_classification never reads it. Meanwhile the language tokens classify to PK (Indic literature), so a title like "Punjabi Cooking Made Easy" would classify PK rather than TX — a language token deciding a subject class. Resolving this properly depends on the deferred language-first key ordering work.

- source_spec: `/Users/davinderpalrehal/Projects/pothi-parivaar/_bmad-output/implementation-artifacts/spec-2-3-lcc-class-map.md`
  summary: Non-Latin-script titles can never match any keyword, so Gurmukhi or Devanagari titles always fall back to a flagged PN.
  evidence: Matching is lowercase Latin substring/boundary only. The story 2.2 analysis established every current title is Latin script (romanized Punjabi included), so this is latent rather than live — but it becomes real the moment a Gurmukhi title is catalogued.

- source_spec: `/Users/davinderpalrehal/Projects/pothi-parivaar/_bmad-output/implementation-artifacts/spec-2-3-lcc-class-map.md`
  summary: Nothing records which books hold a fallback class — a confirmed PN is indistinguishable from a genuine PN classification.
  evidence: The warning is advisory only; confirm() happily PUTs an unedited PN, and class_source is deliberately not persisted. Since the table also assigns PN6790 to comics, there is no way to query the catalog for books that still need a human to set a real class.

- source_spec: `/Users/davinderpalrehal/Projects/pothi-parivaar/_bmad-output/implementation-artifacts/spec-2-3-lcc-class-map.md`
  summary: class_matched_keyword is returned by the API and asserted in tests but never surfaced in the UI.
  evidence: ClassifySuggestDialog reads class_source only. Showing which keyword matched ("matched 'sikh' in the title") would let the librarian judge a suggestion instead of trusting it; otherwise the field is dead weight on the wire.

- source_spec: `/Users/davinderpalrehal/Projects/pothi-parivaar/_bmad-output/implementation-artifacts/spec-2-3-lcc-class-map.md`
  summary: No table-hygiene test guards DOMAIN_LCC_MAP against duplicate or subsumed keyword entries.
  evidence: Under the original substring matching, "sikhism" was fully covered by the later "sikh", "coloring" by "color", and "maths" by "math" — entries that could never change an outcome. Word-boundary matching makes these meaningful again, but nothing prevents a future entry from being silently unreachable.

## Deferred from: code review of spec-catalog-language-filter.md (2026-08-31)

- source_spec: `/Users/davinderpalrehal/Projects/pothi-parivaar/_bmad-output/implementation-artifacts/spec-catalog-language-filter.md`
  summary: No executable verification for any App.vue filter behavior — the language param assembly, the two loadLanguageOptions refresh hooks, and the new stale-selection clear are all verified only by reading the code and by hand.
  evidence: Pure helpers in languages.js are covered by node:test (48 tests), but nothing mounts App.vue, so `Object.assign(params, languageFilterParams(...))` could be replaced with `params.language = languageFilter.value` and the whole suite would stay green. Acceptance criterion "counts reflect the change without a page reload" has no automated check at all. This is a third instance of the repo-wide missing-component-runner gap already recorded from the 2.1 and 1.2 reviews, not a new root cause.
