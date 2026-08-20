# Addendum: Pothi Parivaar Context & Design Notes

*This document captures operational details, technical notes, and physical organization strategies that inform downstream PRD and Architecture.*

---

## 1. Physical Library Organization Strategies (Options & Recommendations)

Organizing 1,000+ books incrementally from a single overflowing shelf into a multi-room system:

### Proposed Flexible Hierarchy
- **Location / Room**: e.g., `Home Office`, `Living Room`, `Kids Bedroom`
- **Unit / Bookcase**: e.g., `Main Shelf`, `Small Shelf A`
- **Shelf / Row**: e.g., `Shelf 1` (Top), `Shelf 2`, `Shelf 3`
- **Optional Tagging / Grouping**:
  - *By Author*: Alphabetical by Author's last name (good for literature, fiction, general collections).
  - *By Topic / Genre*: Broad categories like Science, History, Sikh Heritage / Punjabi Literature, Philosophy, Children's Fiction.
  - *Hybrid Approach (Recommended for Families)*:
    - Dedicated Children & Youth Section (by reading level / series / author).
    - Heritage & Philosophy Section.
    - General Fiction & Non-fiction (Author alphabetical or topic).

---

## 2. Ingestion & Educational Experience

- **Children's Manual Ingestion Flow**:
  - Kids inspect the physical book's title page and colophon (Title, Author, Publication Year, Publisher).
  - Kids type the data in, reinforcing bibliographical literacy.
- **ISBN Fast-Lookup Flow**:
  - Prominent ISBN input field or scanner.
  - Queries open book APIs (e.g. Open Library, Google Books) to autofill cover, summary, genres, page count.
  - Useful for grandparents or bulk cataloging sprints.

---

## 3. Hermes AI Agent Integration (VPS)

- **Architecture**:
  - Pothi Parivaar backend and Hermes Agent run on the same VPS instance.
  - Exposes clean REST API endpoints on `localhost` (e.g., `/api/books/search`, `/api/books/recommend`, `/api/readers/current`).
- **Hermes Skill Capabilities**:
  - `search_library(query, genre, age_appropriate, format)`: Find physical location or digital link.
  - `recommend_book(user_interest, age_group, exclude_read)`: Smart discovery assistant.
  - `get_reading_status(reader_name)`: Track active reading sessions.
