---
id: SPEC-structured-authors
companions:
  - brownfield.md
  - name-rules.md
  - honorifics.md
  - publishers.md
  - ../../planning-artifacts/prds/prd-pothi-parivaar-2026-08-20/prd.md
  - ../../planning-artifacts/architecture/architecture-pothi-parivaar-2026-08-20/ARCHITECTURE-SPINE.md
sources: []
---

> **Canonical contract.** This SPEC and the files in `companions:` are the complete, preservation-validated contract for what to build, test, and validate. Source documents listed in frontmatter are for traceability — consult them only if you need narrative rationale or prose color this contract intentionally omits.

# Structured Authors and Optional Publishers

## Why

**Pain to solve.** The family is already cataloging books. Some titles have more than one author; some (magazines) have a publishing house and no author. Saving a short form (`D. Carnegie`) as the only name throws away the full name, so display style cannot change later and authors and publishers cannot be found as their own records. Honorifics are part of how this library names people: `Dr. Davinder Singh` must read as `Dr. D. Singh`, and `Bhai Sahib Bhai Vir Singh ji` as `BHB V. Singh`, not `D. Singh` / `B. ji`. New titles appear in daily use, so recognition cannot wait on a code change.

## Capabilities

- **CAP-1**
  - **intent:** A family member can record each author as first name, last name, and optional middle name so the full name survives later display changes.
  - **success:** An author with first and last is stored and read back; middle may be omitted; a mononym stores first name and last name as a single space.

- **CAP-2**
  - **intent:** A family member can attach zero or more authors to a book, in a chosen order.
  - **success:** A magazine with no authors saves; a book with two authors stores both in that order; removing one leaves the other.

- **CAP-3**
  - **intent:** The catalog can show a derived short form from stored name parts, including recognized honorifics, without using that short form as the only stored name.
  - **success:** Dale Carnegie displays as `D. Carnegie` while first=`Dale` and last=`Carnegie` remain. `Dr. Davinder Singh` (parts first=`Dr.`, middle=`Davinder`, last=`Singh`) displays as `Dr. D. Singh`. `Bhai Sahib Bhai Vir Singh ji` displays as `BHB V. Singh`. Plato / Madonna / Cher display as those names, not `P.` / `M.` / `C.`. Changing the display rule or the honorific list does not require retyping names.

- **CAP-4**
  - **intent:** A family member or Hermes can still find a book by author text after names are structured.
  - **success:** Keyword search and locate match first name, last name, middle name, the derived short form (including mononym full first name), recognized title tokens, and title abbreviations (`Dr.`, `BHB`).

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

- **CAP-9**
  - **intent:** A household member can maintain the recognized honorific list so new titles are recognized without a code change.
  - **success:** Adding `Bhai Sahib Bhai` / prefix / `BHB` makes the next card for a matching reconstructed name show `BHB V. Singh`; disabling or deleting that row stops that recognition; stored first/middle/last do not change.

## Constraints

- First name is required on every author. Last name is required and may be a single space (mononym). Middle name is optional.
- A book may have zero authors.
- Author order on the book is the display and save order.
- Titles stay inside first/middle/last. No title columns in this work. Identity remains same first+middle+last.
- Short form is derived from the reconstructed token sequence (first + middle tokens + last), after peeling the persisted honorific list, and is never the only copy of the name. Mononym display is the remaining first name as-is (plus any prefix abbreviations).
- Honorific recognition is persisted editable data, seeded from `honorifics.md`. Match longest token sequence first, case-insensitive, optional trailing period. Prefixes peel from the front; suffixes from the end. Empty abbreviation omits that honorific on the card.
- Do not re-run the CAP-7 author-string migration for honorifics. Changing the honorific list does not rewrite stored name parts.
- No login/role gate on the honorific editor in this work.
- Author is its own record; books link to authors. Same first+middle+last reuses one author.
- Publisher is its own record; attaching one to a book is optional. Rules in `publishers.md`.
- ISBN prefill and the one-time author migration use the same split rules in `name-rules.md` and do not create publishers.
- Catalog cards, book detail, add/edit, Hermes locate/recommend, and keyword search must keep working against the new author model.

## Non-goals

- Author or publisher biographies, photos, or authority-file IDs.
- Inventing a first name from an existing short form (`D. Carnegie` stays first=`D.`, last=`Carnegie`).
- A dedicated author-browse or publisher-browse UI in this work.
- Requiring a publisher on any book.
- A second rewrite of stored author rows when honorifics are added or this display rule ships.
- Seeding `Singh`, `Kaur`, or `Guru` as honorifics.
- Role-based admin authentication for the honorific editor.

## Success signal

Save a two-author book and see `D. Carnegie, J. Doe` on the card. Save `Dr. Davinder Singh` and see `Dr. D. Singh`. Save `Bhai Sahib Bhai Vir Singh ji` and see `BHB V. Singh`. Add a new honorific in the editor and see the next card pick it up without changing stored name parts. Save a magazine with no authors and an optional publisher. Save Cher and see `Cher`, not `C.`. Two books with the same author name parts share one author record.

## Assumptions

- Current derived form ignores leftover personal middle tokens: Dale B. Carnegie → `D. Carnegie`.
- Multiple authors display as comma-separated short forms in listed order.
- Create and edit require title; authors and publisher are optional.
- Empty or missing `author` string on an existing book yields zero authors.
- `"Unknown Author"` from ISBN is split as first=`Unknown`, last=`Author`.
- A book links to at most one publisher at this stage.
- A publisher is identified by a single organization name; same name reuses one record.
- ISBN prefill and the author migration do not create or attach publishers.
- ISBN/migration split stays comma-then-space; honorifics are recognized at display (and search against the derived form), not by rewriting parts.
- Gyani and Giani share abbreviation `Gyani`. Dr/Doctor and Prof/Professor share `Dr.` / `Prof.`.
- Bhai alone stays `Bhai` on the card. Sardar → `S.`. Sardarni → `Sdn.`. Bibi Sahib Bibi → `BSB`. Singh Sahib → `S.S.`. Bhai Sahib → `B.S.`.
- The honorific editor may change after testing; storage stays name parts until a later spec update says otherwise.
