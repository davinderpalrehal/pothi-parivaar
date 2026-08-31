# Epic 2 Context: LCC shelf key

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Give every catalogued book a Library of Congress–style shelf key — class letters plus a Cutter for the work — and surface it as a badge on the catalog card, so the physical collection can be ordered and found on a shelf. Classification must work for titles with no ISBN (small-press and self-published), so it derives from title, subjects/genres and structured authors rather than external lookup. Story 2.1 shipped the first pass of this (suggest-then-confirm classification plus the card badge). Measurement against the live collection then showed the key is not yet doing its job — half the books share a key — so the remaining work is being taken in narrow, independently shippable slices. Story 2.2 is now scoped to one of them only: capturing what language a book is in. The other slices (better subject classes, a collision-proof Cutter, language-first key ordering with a re-key migration, and catalog data cleanup) are recorded as deferred future work, not part of this story. Note on sources: the PRD, brief and architecture spine all predate this epic and say nothing about classification or call numbers; everything specific here comes from the epic stub, the shipped 2.1 work, and the production-data analysis.

## Stories

- Story 2.1: LCC Cutter shelf-key badge (done)
- Story 2.2: Shelf-key language grouping

## Requirements & Constraints

- Classification must never require an ISBN or block on an external lookup. The catalog treats ISBN as optional at data-entry level and that must not regress into a hidden dependency.
- Language is a first-class attribute of a book, not a derived one. Books need a **primary** language for shelving plus **optional additional** languages — real records in the collection are multilingual (an English/Sanskrit title, a `mul` title), so a single scalar is insufficient. Codes are ISO 639-3.
- **Nothing about language may be guessed or inferred.** Script is not a signal here: every title in the collection is in Latin script, including romanized Punjabi. A value is either captured from a metadata source or entered by a human.
- Automatic language coverage is known and low: measured against the whole collection, an external record yields a language for roughly a quarter of books. Most books either have no ISBN at all or no matching record. The design must therefore assume **manual entry is the main path**, with a bulk-assign screen for everything lookup cannot resolve — not a background enrichment job that quietly leaves most books blank.
- A second metadata source is not free: the unauthenticated Google Books endpoint currently fails on shared-IP quota, so treating it as a fallback requires provisioning an API key.
- Catalog search and filtering must stay fast (sub-100ms) at 1,000-book scale; language will become a grouping/filter dimension.
- Success criteria for classification *accuracy* are not defined in any planning source. Do not invent thresholds.

## Technical Decisions

Locked decisions from the collision analysis — binding for this epic even where the work implementing them is deferred:

- **Key ordering is Language → Subject → Author**, with language as the outermost shelf block.
- The key is stored as **separate components, never one opaque string**, so the catalog can group and filter on each part independently, with a uniqueness constraint spanning them.
- **Uniqueness is enforced against the shelflist at assign time**, by widening the key (extending the work mark) until it is free — not by adding more entropy to the algorithm. A consequence: classification stops being a pure function and gains a database session, which invalidates the existing purity assumptions in the classification tests.
- The `Book` language field is an **additive migration**, following the same pattern already used when the call-number columns were added to the legacy-DB upgrade path.
- ISBN lookup switches to the OpenLibrary `details` view (or calls both), which returns `languages` and richer subjects; the currently-used view omits language entirely.
- Data cleanup (non-person author records that are really publishers or honorifics, and one duplicated book record) must land **before** any re-key migration, or it bakes confidently-wrong keys into the collection.

Still genuinely open — ask, do not decide unilaterally:

- Whether the bulk-assign UI shows ISO codes or friendly language names, and which languages get quick-pick buttons.
- How multi-language (`mul`) books shelve: primary language only, or their own block.
- Whether series volumes get an explicit part designation in the key.

## UX & Interaction Patterns

- This epic established a **suggest-then-confirm** pattern: a computed shelf key is presented for human approval and editing and is never auto-persisted; confirmation flows through the normal book-update path. Language capture should respect the same principle — a looked-up language is a proposal, not a fact written behind the user's back.
- Language must be enterable manually on both the add-book and edit-book forms, alongside the existing structured-author entry.
- A **bulk-assign screen** covers the majority of books that lookup cannot resolve; it is the primary tool for filling the collection, not an admin afterthought.
- The catalog card already carries badge-style chips (physical location, call number), which is the established shape for surfacing shelf metadata.

## Cross-Story Dependencies

- Story 2.2 depends on Story 2.1's persisted call-number fields and badge only for display context; language capture itself is independent of the Cutter algorithm and can ship on its own.
- Cutter derivation depends on the structured-author model from the authors epic (zero, one, or many authors; mononyms), not on a raw author string.
- Story 2.2 changes the OpenLibrary request shape; the authors epic's ISBN author-name-split story touches the same lookup path, so the two should be coordinated to avoid conflicting edits.
- Deferred follow-on work (tracked in `deferred-work.md`) has a strict order: subject-class map and the new Cutter can ship independently, but **language-first key ordering and the one-shot re-key migration require language capture, the class map, and the new Cutter to all have landed** — holding it avoids re-keying the collection twice. Data cleanup must precede that migration.
