## Deferred from: code review of spec-reader-profiles-and-progress.md (2026-08-20)

- Catalog `GET /books` default `limit=100` (`app/api/books.py:26`) — pre-existing list default; a 1,000-book library is silently truncated on the catalog grid. Not introduced by the reader-profile change.
