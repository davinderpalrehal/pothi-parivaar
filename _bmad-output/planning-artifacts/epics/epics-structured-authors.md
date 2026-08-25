# Structured Authors and Optional Publishers

Source spec: `_bmad-output/specs/spec-structured-authors/SPEC.md`

## Epic 1: Structured Authors and Optional Publishers

Replace the single `Book.author` string with first-class author and publisher records. Authors are optional (magazines). Publisher is optional. Display stays a derived short form.

### Story 1.1: Author publisher persistence

Author and publisher tables, book links, API read/write, one-time migration of existing `Book.author` strings, search/Hermes against name parts. Keep a derived `author` short-form on reads so the current Vue cards still render. CAP-1, CAP-2, CAP-3 (read), CAP-4, CAP-6, CAP-7, CAP-8.

### Story 1.2: Author add edit UI

Add Book and Book Detail collect zero or more structured authors (first, last, optional middle) and an optional publisher. Mononym last name is a space; display is `Plato` not `P.`. CAP-1, CAP-2, CAP-3 (write UI), CAP-8.

### Story 1.3: ISBN author name split

ISBN / Open Library prefill splits author strings per `name-rules.md`. Lookup stays advisory and does not create publishers. CAP-5.
