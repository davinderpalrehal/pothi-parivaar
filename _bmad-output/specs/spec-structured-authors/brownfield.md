# Brownfield — Author as one string

Live catalog (2026-08-23) stores and shows a single `Book.author` string. This spec replaces that string with author records and book–author links. CAP-7 is the one-time conversion.

## Storage and API

- `app/models.py`: `Book.author`, `BookCreate.author`, `BookRead.author` are required `str`; `BookUpdate.author` is optional `str`.
- Create requires `title` + `author` (`spec-catalog-and-dual-ingestion`, FR-1/FR-5). After this spec, create requires title only; authors are optional.
- Architecture spine ERD: `BOOK.author` is `string`. After this spec, `BOOK` links to `AUTHOR`.
- PRD addendum: `author: String (Required)`. PRD FR-1 wording is `Author(s)`.

## Ingestion

- `app/services/isbn_service.py`: Open Library `authors[].name` values are joined with `", "` into one string, or `"Unknown Author"`.
- After this spec, each Open Library name (and that joined string if still used) is split per `name-rules.md`.
- ISBN lookup stays advisory prefill; `POST /books` must not call ISBN (AD-4).

## Surfaces that read `book.author`

- Add Book and Book Detail edit: one required author field — becomes zero or more structured authors.
- Book cards, catalog search placeholder, Reader Tracker subtitles — show derived short forms.
- `GET /api/v1/books?q=` matches `Book.author` via ILIKE — must match author name parts and short form.
- Hermes recommend and locate return `author` and locate also ILIKE-matches `Book.author`.

## Current family practice

- Manual save style: first initial + last name (`Dale Carnegie` → `D. Carnegie`).
- Some titles have multiple authors in one string.
- Magazines may have no personal author and no publisher field today. Publisher is new (CAP-8); optional; not inferred by the author migration.

## One-time conversion (CAP-7)

Run once against existing `Book.author` values using `name-rules.md`. Afterward, `Book.author` is not the source of truth. `D. Carnegie` becomes first=`D.`, last=`Carnegie` — `Dale` is not recovered.

Honorific display (CAP-3 update, CAP-9) does **not** run a second conversion. Rows already split keep their first/middle/last; only the derived short form changes. There is no Settings screen today — CAP-9 adds the honorific list editor.
