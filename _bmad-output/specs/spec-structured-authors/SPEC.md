---
id: SPEC-structured-authors
companions:
  - brownfield.md
  - name-rules.md
  - publishers.md
  - ../../planning-artifacts/prds/prd-pothi-parivaar-2026-08-20/prd.md
  - ../../planning-artifacts/architecture/architecture-pothi-parivaar-2026-08-20/ARCHITECTURE-SPINE.md
sources: []
---

> **Canonical contract.** This SPEC and the files in `companions:` are the complete, preservation-validated contract for what to build, test, and validate. Source documents listed in frontmatter are for traceability — consult them only if you need narrative rationale or prose color this contract intentionally omits.

# Structured Authors and Optional Publishers

## Why

**Pain to solve.** The family is already cataloging books. Some titles have more than one author; some (magazines) have a publishing house and no author. Saving a short form (`D. Carnegie`) as the only name throws away the full name, so display style cannot change later and authors and publishers cannot be found as their own records.

## Capabilities

- **CAP-1**
  - **intent:** A family member can record each author as first name, last name, and optional middle name so the full name survives later display changes.
  - **success:** An author with first and last is stored and read back; middle may be omitted; a mononym stores first name and last name as a single space.

- **CAP-2**
  - **intent:** A family member can attach zero or more authors to a book, in a chosen order.
  - **success:** A magazine with no authors saves; a book with two authors stores both in that order; removing one leaves the other.

- **CAP-3**
  - **intent:** The catalog can show a derived short form from stored name parts without using that short form as the only stored name.
  - **success:** Dale Carnegie displays as `D. Carnegie` while first=`Dale` and last=`Carnegie` remain. Plato / Madonna / Cher display as those names, not `P.` / `M.` / `C.`. Changing the display rule later does not require retyping names.

- **CAP-4**
  - **intent:** A family member or Hermes can still find a book by author text after names are structured.
  - **success:** Keyword search and locate match first name, last name, middle name, and the derived short form (including the mononym full first name).

- **CAP-5**
  - **intent:** ISBN lookup can prefill structured authors that stay editable before save.
  - **success:** Open Library author strings are split per `name-rules.md`; lookup does not persist a book; the user can change every name part before save.

- **CAP-6**
  - **intent:** Authors exist as their own records so a name can be found and reused across books, including by a later author search.
  - **success:** Two books that share one author point at the same author record; that record is queryable by first, middle, and last name.

- **CAP-7**
  - **intent:** Existing catalog rows keep their authors after a one-time conversion of the stored author string.
  - **success:** A one-time script applies `name-rules.md` to every existing `Book.author` value; afterward books no longer depend on that string as the source of truth.

- **CAP-8**
  - **intent:** Publishers exist as their own records so a book may optionally name a publishing house, especially when it has no author.
  - **success:** A book saves with no publisher; a book can link to one publisher; two books that share a publisher name point at the same publisher record.

## Constraints

- First name is required on every author. Last name is required and may be a single space (mononym). Middle name is optional.
- A book may have zero authors.
- Author order on the book is the display and save order.
- The short form is derived from stored name parts and is never the only copy of the name. Mononym display is the first name as-is.
- Author is its own record; books link to authors. Same first+middle+last reuses one author.
- Publisher is its own record; attaching one to a book is optional. Rules in `publishers.md`.
- ISBN prefill and the one-time author migration use the same split rules in `name-rules.md` and do not create publishers.
- Catalog cards, book detail, add/edit, Hermes locate/recommend, and keyword search must keep working against the new author model.

## Non-goals

- Changing the current short-form style for multi-part names in this work.
- Author or publisher biographies, photos, or authority-file IDs.
- Inventing a first name from an existing short form (`D. Carnegie` stays first=`D.`, last=`Carnegie`).
- A dedicated author-browse or publisher-browse UI in this work.
- Requiring a publisher on any book.

## Success signal

Save a two-author book and see `D. Carnegie, J. Doe` on the card. Save a magazine with no authors and an optional publisher. Save Cher and see `Cher`, not `C.`. Run the one-time conversion on an existing `D. Carnegie` row and still find the book by search. Two books with the same author name parts share one author record.

## Assumptions

- Current derived form ignores middle name: Dale B. Carnegie → `D. Carnegie`.
- Multiple authors display as comma-separated short forms in listed order.
- Create and edit require title; authors and publisher are optional.
- Empty or missing `author` string on an existing book yields zero authors.
- `"Unknown Author"` from ISBN is split as first=`Unknown`, last=`Author`.
- A book links to at most one publisher at this stage.
- A publisher is identified by a single organization name; same name reuses one record.
- ISBN prefill and the author migration do not create or attach publishers.
