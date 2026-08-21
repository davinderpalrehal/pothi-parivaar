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
