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
