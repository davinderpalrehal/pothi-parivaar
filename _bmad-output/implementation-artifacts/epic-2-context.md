# Epic 2 Context: LCC shelf key

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Once a book is saved to the catalog, assign it a Library of Congress Classification (class letters + number) plus a Cutter number for the work, and surface that call number as a shelf-key badge on the catalog card. Classification must be derivable from title, authors, subjects/genres, and optional publisher alone — it must never require an ISBN, since many titles in this collection (small-press, self-published) have none. Note: the PRD, architecture spine, and brief all predate this epic and contain no material on book classification, call numbers, or LCC/Cutter logic — this section is compiled almost entirely from the epic stub itself, and the gaps below are real gaps, not omissions from scoping.

## Stories

- Story 2.1: LCC Cutter shelf-key badge

## Requirements & Constraints

- Manual book creation and editing must remain fully independent of any external/ISBN lookup service — classification logic must follow the same rule and never block on or require ISBN data.
- The catalog already treats ISBN as fully optional at the data-entry level; classification cannot regress that by becoming a hidden ISBN dependency.
- Catalog search/filter performance must stay fast (sub-100ms) at 1,000+ book scale — relevant if shelf-key computation happens at read time rather than being persisted.
- No planning-artifact source defines success criteria, accuracy expectations, or acceptance thresholds for the classification itself; none should be assumed.

## Technical Decisions

- Books already carry a `genres_tags` field (JSON array of subject/genre strings, e.g. `["History", "Space", "Fiction"]`) — this is the existing data available as classification input; no separate LCSH/subject-authority field exists.
- Authors are first-class structured records (from a separate, already-implemented epic), each with first/last/optional-middle name parts, and a book may have zero or many authors, including mononym authors (last name only). Any Cutter-number-by-author logic must account for zero-author and multi-author cases using this structure, not a raw author string.
- ISBN lookup is architecturally a separate, advisory-only service (`app/api/isbn.py` / `isbn_service.py`), decoupled from core book creation. No architectural decision exists yet for where classification logic should live (service layer, model hook, background job, etc.) — this is undecided in planning docs.
- No data model fields, API contracts, or persistence strategy for a call number / LCC class / Cutter number exist in any planning artifact.

## UX & Interaction Patterns

- The book card already displays a badge for physical shelf location (room/unit/shelf), establishing a precedent for badge-style metadata on the catalog card. No planning artifact defines a badge style, copy format (full call number vs. class only), or placement for a classification badge specifically.

## Cross-Story Dependencies

- Depends on the structured-author data model (first/last/middle name parts, zero-or-many authors per book) from the prior Structured Authors epic, since Cutter-number derivation needs parsed author name parts rather than a single author string.
- Explicitly must not depend on the ISBN lookup epic/service — classification is scoped to work without it.
- Key decisions are still open per the story stub and unresolved by any planning artifact: manual override vs. auto-only vs. suggest-then-confirm; which author drives the Cutter when there are zero or many; persist-on-write vs. compute-on-read; and badge copy (full call number vs. class only). These should be confirmed with the user/PM before implementation, not assumed.
