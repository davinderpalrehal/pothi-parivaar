# Epic 1 Context: Structured Authors and Optional Publishers

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Replace the catalog’s single stored author string with first-class author records (and optional publisher records) so full names survive later display changes, magazines can have zero authors, and the same person or house can be reused across books. Family members still see the familiar derived short form on cards; keyword search and Hermes locate/recommend keep working against name parts and that short form. ISBN prefill stays advisory and editable. Existing rows are converted once using the same name-split rules; short forms like `D. Carnegie` are not expanded back to full given names.

## Stories

- Story 1.1: Author publisher persistence
- Story 1.2: Author add edit UI
- Story 1.3: ISBN author name split

## Requirements & Constraints

Authors: first name required; last name required and may be a single space (mononym); middle optional. A book may have zero or more authors in a chosen order (display and save order). Same first + middle + last reuses one author record.

Short form is always derived, never the only stored name. Multi-part names: first character of first name + `. ` + last name; middle is omitted from display (`Dale B. Carnegie` → `D. Carnegie`). Mononym (last name is one space): show first name as-is (`Plato`, not `P.`). Multiple authors: comma-separated short forms in book-author order.

Search and Hermes locate must match first, middle, last, and the derived short form (including the mononym’s full first name). Create/edit still require title; authors and publisher are optional. Empty/missing legacy author string → zero authors. Do not invent a given name from an initial (`D. Carnegie` stays first=`D.`).

Publishers: optional; at most one per book; identified by a single organization name (same name reuses one record). Magazines may name a house with no personal authors. ISBN lookup and the one-time author conversion must not create or attach publishers.

Out of this epic: new short-form style for multi-part names; biographies, photos, authority IDs; author/publisher browse UIs; required publisher.

Success in one pass: two-author card shows `D. Carnegie, J. Doe`; magazine with no authors and optional publisher saves; Cher displays as `Cher`; migrated `D. Carnegie` still searchable; two books with the same name parts share one author.

## Technical Decisions

Manual book create is independent of ISBN lookup; lookup is advisory prefill only and must not persist a book. API reads should still expose a derived `author` short-form string so existing catalog cards keep rendering. Authors and publishers are their own records with book links (ordered authors; optional single publisher). One-time conversion applies the name-split rules to every existing `Book.author` value; afterward that string is not the source of truth.

Name split (ISBN prefill and migration share this): split the string on commas, trim, drop empties; each segment split on ASCII space. No tokens → skip. One token → first = token, last = one space, no middle. Two or more → first = first token, last = last token, middle = leftover tokens joined by a single space (or omitted). `"Unknown Author"` → first=`Unknown`, last=`Author`.

## UX & Interaction Patterns

Add Book and Book Detail collect zero or more structured authors (first, last, optional middle) and an optional publisher instead of one required author field. ISBN lookup still autofills metadata; split author strings remain fully editable before save; lookup miss or no ISBN still allows manual save. Cards, book detail, reader-tracker subtitles, and catalog search continue to show derived short forms, not raw name parts as the primary label.

## Cross-Story Dependencies

1.2 (write UI) and 1.3 (ISBN split) depend on 1.1 persistence, links, derived read `author`, search/Hermes matching, and reuse of author/publisher records. 1.3 must use the same split rules as the 1.1 migration and must not create publishers. Catalog cards can stay as they are if reads keep the derived short form.
