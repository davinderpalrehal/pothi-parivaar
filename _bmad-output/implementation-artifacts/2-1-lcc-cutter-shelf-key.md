# Stub — 2.1 LCC Cutter shelf-key badge

**Priority:** high  
**Status:** backlog stub (not ready-for-dev)  
**Tomorrow:** run `[BD] Build` (`bmad-build`) in a **fresh chat** with this file as the intent.

## Intent (draft)

Once a book is in the catalog, show a **shelf-key badge** on the book card: Library of Congress Classification (class letters + number) plus a **Cutter** for the work. Many titles have **no ISBN** (small houses); classification must use title, authors, subjects/genres, and optional publisher — never require ISBN lookup.

## Open questions for Build (do not invent answers tomorrow without asking)

- Manual override vs auto-only vs “suggest then confirm”.
- Which author is used for Cutter when there are zero or many authors (title Cutter?).
- Persist on the book row vs recompute on read.
- Badge copy: full call number vs class only.

## Likely touchpoints (investigation only)

- `app/models.py` / book read schema
- `frontend/src/components/BookCard.vue` (existing location chip pattern)
- No ISBN-only path: `app/api/isbn.py` stays optional

## Out of scope for this stub

- Replacing physical Room/Unit/Shelf
- Full LCSH authority control
